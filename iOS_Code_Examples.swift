// 📱 Wikipedia GeoHist - iOS Swift Code Examples

import SwiftUI
import MapKit
import Combine
import Foundation

// MARK: - Models

struct Person: Codable, Identifiable, Hashable {
    let id = UUID()
    let searchTerm: String
    let fullName: String
    let nationality: String
    let birthDate: String
    let birthPlace: String
    let deathDate: String?
    let deathPlace: String?
    let century: String
    let coordinates: Coordinate?
    let wikipediaURL: String
    let imageURL: String?
    
    var isAlive: Bool {
        return deathDate == nil || deathDate == "Não Informado"
    }
    
    var centuryNumber: Int {
        return Int(century.replacingOccurrences(of: " a.C.", with: "")) ?? 0
    }
}

struct Coordinate: Codable, Hashable {
    let latitude: Double
    let longitude: Double
    
    var isValid: Bool {
        return latitude >= -90 && latitude <= 90 && 
               longitude >= -180 && longitude <= 180
    }
    
    var clLocationCoordinate2D: CLLocationCoordinate2D {
        return CLLocationCoordinate2D(latitude: latitude, longitude: longitude)
    }
}

struct Session: Codable, Identifiable {
    let id = UUID()
    let name: String
    let createdAt: Date
    let people: [Person]
    
    var peopleCount: Int { people.count }
    var countriesCount: Int { Set(people.map(\.nationality)).count }
}

// MARK: - Services

class WikipediaService: ObservableObject {
    private let session = URLSession.shared
    private let baseURL = "https://pt.wikipedia.org"
    private var cancellables = Set<AnyCancellable>()
    
    func searchPerson(_ searchTerm: String) -> AnyPublisher<Person?, Error> {
        guard let encodedTerm = searchTerm.addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed),
              let url = URL(string: "\(baseURL)/w/index.php?search=\(encodedTerm)&title=Especial:Pesquisar&profile=advanced&fulltext=1&ns0=1") else {
            return Fail(error: URLError(.badURL))
                .eraseToAnyPublisher()
        }
        
        var request = URLRequest(url: url)
        request.setValue("Wikipedia GeoHist iOS/1.0", forHTTPHeaderField: "User-Agent")
        
        return session.dataTaskPublisher(for: request)
            .map(\.data)
            .decode(type: WikipediaSearchResponse.self, decoder: JSONDecoder())
            .map { response in
                // Processa resposta da Wikipedia
                return self.parseWikipediaResponse(response, searchTerm: searchTerm)
            }
            .eraseToAnyPublisher()
    }
    
    private func parseWikipediaResponse(_ response: WikipediaSearchResponse, searchTerm: String) -> Person? {
        // Implementa lógica de parsing similar ao Python
        // Retorna Person ou nil
        return nil
    }
}

class WikidataService: ObservableObject {
    private let sparqlEndpoint = "https://query.wikidata.org/sparql"
    private let session = URLSession.shared
    
    func fetchPersonDetails(_ name: String) -> AnyPublisher<PersonDetails?, Error> {
        let query = """
        SELECT ?personLabel ?birthDate ?birthPlaceLabel ?deathDate ?deathPlaceLabel ?countryLabel ?image ?coord ?countryCoord WHERE {
          ?person rdfs:label "\(name)"@pt.
          ?person wdt:P31 wd:Q5.
          OPTIONAL { ?person wdt:P569 ?birthDate. }
          OPTIONAL {
              ?person wdt:P19 ?birthPlace.
              OPTIONAL {?birthPlace rdfs:label ?birthPlaceLabel. FILTER(LANG(?birthPlaceLabel) = "pt") }
              OPTIONAL { ?birthPlace wdt:P625 ?coord. }
          }
          OPTIONAL { ?person wdt:P570 ?deathDate. }
          OPTIONAL {
              ?person wdt:P20 ?deathPlace.
              OPTIONAL {?deathPlace rdfs:label ?deathPlaceLabel. FILTER(LANG(?deathPlaceLabel) = "pt") }
          }
          OPTIONAL {
              ?person wdt:P27 ?country.
              OPTIONAL {?country rdfs:label ?countryLabel. FILTER(LANG(?countryLabel) = "pt") }
              OPTIONAL { ?country wdt:P625 ?countryCoord. }
          }
          OPTIONAL { ?person wdt:P18 ?image. }
        }
        LIMIT 1
        """
        
        guard let url = URL(string: sparqlEndpoint) else {
            return Fail(error: URLError(.badURL)).eraseToAnyPublisher()
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/x-www-form-urlencoded", forHTTPHeaderField: "Content-Type")
        request.setValue("Wikipedia GeoHist iOS/1.0", forHTTPHeaderField: "User-Agent")
        request.httpBody = "query=\(query)&format=json".data(using: .utf8)
        
        return session.dataTaskPublisher(for: request)
            .map(\.data)
            .decode(type: SPARQLResponse.self, decoder: JSONDecoder())
            .map { response in
                return self.parseSPARQLResponse(response)
            }
            .eraseToAnyPublisher()
    }
    
    private func parseSPARQLResponse(_ response: SPARQLResponse) -> PersonDetails? {
        // Implementa parsing da resposta SPARQL
        return nil
    }
}

// MARK: - ViewModels

class SearchViewModel: ObservableObject {
    @Published var searchText = ""
    @Published var searchResults: [Person] = []
    @Published var isLoading = false
    @Published var errorMessage: String?
    
    private let wikipediaService = WikipediaService()
    private let wikidataService = WikidataService()
    private var cancellables = Set<AnyCancellable>()
    
    func searchPerson() {
        guard !searchText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else { return }
        
        isLoading = true
        errorMessage = nil
        
        wikipediaService.searchPerson(searchText)
            .receive(on: DispatchQueue.main)
            .sink(
                receiveCompletion: { [weak self] completion in
                    self?.isLoading = false
                    if case .failure(let error) = completion {
                        self?.errorMessage = error.localizedDescription
                    }
                },
                receiveValue: { [weak self] person in
                    if let person = person {
                        self?.searchResults.append(person)
                    }
                }
            )
            .store(in: &cancellables)
    }
}

class MapViewModel: ObservableObject {
    @Published var people: [Person] = []
    @Published var filteredPeople: [Person] = []
    @Published var selectedCenturies: Set<String> = []
    @Published var selectedCountries: Set<String> = []
    @Published var mapRegion = MKCoordinateRegion(
        center: CLLocationCoordinate2D(latitude: 0, longitude: 0),
        span: MKCoordinateSpan(latitudeDelta: 180, longitudeDelta: 360)
    )
    
    var availableCenturies: [String] {
        return Array(Set(people.map(\.century))).sorted()
    }
    
    var availableCountries: [String] {
        return Array(Set(people.map(\.nationality))).sorted()
    }
    
    func applyFilters() {
        filteredPeople = people.filter { person in
            let centuryMatch = selectedCenturies.isEmpty || selectedCenturies.contains(person.century)
            let countryMatch = selectedCountries.isEmpty || selectedCountries.contains(person.nationality)
            return centuryMatch && countryMatch
        }
        
        updateMapRegion()
    }
    
    private func updateMapRegion() {
        let validCoordinates = filteredPeople.compactMap { $0.coordinates?.clLocationCoordinate2D }
        
        guard !validCoordinates.isEmpty else { return }
        
        let minLat = validCoordinates.map(\.latitude).min() ?? 0
        let maxLat = validCoordinates.map(\.latitude).max() ?? 0
        let minLon = validCoordinates.map(\.longitude).min() ?? 0
        let maxLon = validCoordinates.map(\.longitude).max() ?? 0
        
        let center = CLLocationCoordinate2D(
            latitude: (minLat + maxLat) / 2,
            longitude: (minLon + maxLon) / 2
        )
        
        let span = MKCoordinateSpan(
            latitudeDelta: max(maxLat - minLat, 0.1) * 1.2,
            longitudeDelta: max(maxLon - minLon, 0.1) * 1.2
        )
        
        mapRegion = MKCoordinateRegion(center: center, span: span)
    }
}

// MARK: - Views

struct ContentView: View {
    @StateObject private var searchViewModel = SearchViewModel()
    @StateObject private var mapViewModel = MapViewModel()
    
    var body: some View {
        TabView {
            SearchView()
                .environmentObject(searchViewModel)
                .tabItem {
                    Image(systemName: "magnifyingglass")
                    Text("Buscar")
                }
            
            MapView()
                .environmentObject(mapViewModel)
                .tabItem {
                    Image(systemName: "map")
                    Text("Mapa")
                }
            
            SessionsView()
                .tabItem {
                    Image(systemName: "folder")
                    Text("Sessões")
                }
            
            SettingsView()
                .tabItem {
                    Image(systemName: "gear")
                    Text("Configurações")
                }
        }
    }
}

struct SearchView: View {
    @EnvironmentObject var viewModel: SearchViewModel
    
    var body: some View {
        NavigationView {
            VStack {
                // Campo de busca
                HStack {
                    TextField("Digite o nome da personalidade", text: $viewModel.searchText)
                        .textFieldStyle(RoundedBorderTextFieldStyle())
                        .onSubmit {
                            viewModel.searchPerson()
                        }
                    
                    Button("Buscar") {
                        viewModel.searchPerson()
                    }
                    .disabled(viewModel.isLoading)
                }
                .padding()
                
                // Indicador de carregamento
                if viewModel.isLoading {
                    ProgressView("Buscando...")
                        .padding()
                }
                
                // Mensagem de erro
                if let errorMessage = viewModel.errorMessage {
                    Text(errorMessage)
                        .foregroundColor(.red)
                        .padding()
                }
                
                // Resultados
                List(viewModel.searchResults) { person in
                    PersonRowView(person: person)
                }
                
                Spacer()
            }
            .navigationTitle("Buscar Personalidades")
        }
    }
}

struct PersonRowView: View {
    let person: Person
    
    var body: some View {
        HStack {
            // Imagem da pessoa (placeholder)
            AsyncImage(url: URL(string: person.imageURL ?? "")) { image in
                image
                    .resizable()
                    .aspectRatio(contentMode: .fill)
            } placeholder: {
                Rectangle()
                    .fill(Color.gray.opacity(0.3))
            }
            .frame(width: 60, height: 60)
            .clipShape(Circle())
            
            VStack(alignment: .leading, spacing: 4) {
                Text(person.fullName)
                    .font(.headline)
                
                Text(person.nationality)
                    .font(.subheadline)
                    .foregroundColor(.secondary)
                
                Text("Século \(person.century)")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            
            Spacer()
            
            // Indicador de coordenadas válidas
            if person.coordinates?.isValid == true {
                Image(systemName: "location.fill")
                    .foregroundColor(.green)
            } else {
                Image(systemName: "location.slash")
                    .foregroundColor(.red)
            }
        }
        .padding(.vertical, 4)
    }
}

struct MapView: View {
    @EnvironmentObject var viewModel: MapViewModel
    
    var body: some View {
        NavigationView {
            VStack {
                // Filtros
                FilterControlsView()
                    .environmentObject(viewModel)
                
                // Mapa
                Map(coordinateRegion: $viewModel.mapRegion, 
                    annotationItems: viewModel.filteredPeople.compactMap { person in
                        guard let coord = person.coordinates, coord.isValid else { return nil }
                        return PersonMapAnnotation(person: person, coordinate: coord)
                    }) { annotation in
                    MapAnnotation(coordinate: annotation.coordinate.clLocationCoordinate2D) {
                        PersonMapPin(person: annotation.person)
                    }
                }
                .ignoresSafeArea(edges: .bottom)
            }
            .navigationTitle("Mapa Histórico")
            .navigationBarTitleDisplayMode(.inline)
        }
    }
}

struct PersonMapPin: View {
    let person: Person
    @State private var showingDetail = false
    
    var body: some View {
        Button {
            showingDetail = true
        } label: {
            VStack {
                Image(systemName: "person.circle.fill")
                    .font(.title2)
                    .foregroundColor(.blue)
                    .background(Color.white)
                    .clipShape(Circle())
                    .shadow(radius: 3)
                
                Text(person.fullName.components(separatedBy: " ").first ?? "")
                    .font(.caption2)
                    .padding(2)
                    .background(Color.white.opacity(0.8))
                    .cornerRadius(4)
            }
        }
        .sheet(isPresented: $showingDetail) {
            PersonDetailView(person: person)
        }
    }
}

struct PersonDetailView: View {
    let person: Person
    @Environment(\.dismiss) private var dismiss
    
    var body: some View {
        NavigationView {
            ScrollView {
                VStack(alignment: .leading, spacing: 16) {
                    // Imagem
                    AsyncImage(url: URL(string: person.imageURL ?? "")) { image in
                        image
                            .resizable()
                            .aspectRatio(contentMode: .fit)
                    } placeholder: {
                        Rectangle()
                            .fill(Color.gray.opacity(0.3))
                            .aspectRatio(1, contentMode: .fit)
                    }
                    .frame(maxHeight: 300)
                    .cornerRadius(12)
                    
                    // Informações
                    VStack(alignment: .leading, spacing: 12) {
                        DetailRow(title: "Nome Completo", value: person.fullName)
                        DetailRow(title: "Nacionalidade", value: person.nationality)
                        DetailRow(title: "Nascimento", value: "\(person.birthDate) - \(person.birthPlace)")
                        
                        if let deathDate = person.deathDate, deathDate != "Não Informado" {
                            DetailRow(title: "Falecimento", value: "\(deathDate) - \(person.deathPlace ?? "")")
                        }
                        
                        DetailRow(title: "Século", value: person.century)
                        
                        if let coord = person.coordinates, coord.isValid {
                            DetailRow(title: "Coordenadas", value: "\(coord.latitude), \(coord.longitude)")
                        }
                    }
                    
                    // Link para Wikipedia
                    Link("Ver na Wikipedia", destination: URL(string: person.wikipediaURL)!)
                        .buttonStyle(.borderedProminent)
                }
                .padding()
            }
            .navigationTitle(person.fullName)
            .navigationBarTitleDisplayMode(.large)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Fechar") {
                        dismiss()
                    }
                }
            }
        }
    }
}

struct DetailRow: View {
    let title: String
    let value: String
    
    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(title)
                .font(.caption)
                .foregroundColor(.secondary)
            Text(value)
                .font(.body)
        }
    }
}

// MARK: - Supporting Types

struct PersonMapAnnotation: Identifiable {
    let id = UUID()
    let person: Person
    let coordinate: Coordinate
}

struct WikipediaSearchResponse: Codable {
    // Define estrutura da resposta da Wikipedia
}

struct SPARQLResponse: Codable {
    // Define estrutura da resposta SPARQL
}

struct PersonDetails: Codable {
    // Define estrutura dos detalhes da pessoa
}

struct FilterControlsView: View {
    @EnvironmentObject var viewModel: MapViewModel
    
    var body: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack {
                // Filtro por século
                Menu("Séculos") {
                    ForEach(viewModel.availableCenturies, id: \.self) { century in
                        Button {
                            if viewModel.selectedCenturies.contains(century) {
                                viewModel.selectedCenturies.remove(century)
                            } else {
                                viewModel.selectedCenturies.insert(century)
                            }
                            viewModel.applyFilters()
                        } label: {
                            HStack {
                                Text("Século \(century)")
                                if viewModel.selectedCenturies.contains(century) {
                                    Image(systemName: "checkmark")
                                }
                            }
                        }
                    }
                }
                .buttonStyle(.bordered)
                
                // Filtro por país
                Menu("Países") {
                    ForEach(viewModel.availableCountries, id: \.self) { country in
                        Button {
                            if viewModel.selectedCountries.contains(country) {
                                viewModel.selectedCountries.remove(country)
                            } else {
                                viewModel.selectedCountries.insert(country)
                            }
                            viewModel.applyFilters()
                        } label: {
                            HStack {
                                Text(country)
                                if viewModel.selectedCountries.contains(country) {
                                    Image(systemName: "checkmark")
                                }
                            }
                        }
                    }
                }
                .buttonStyle(.bordered)
            }
            .padding(.horizontal)
        }
    }
}

struct SessionsView: View {
    var body: some View {
        NavigationView {
            Text("Sessões - Em desenvolvimento")
                .navigationTitle("Sessões")
        }
    }
}

struct SettingsView: View {
    var body: some View {
        NavigationView {
            Text("Configurações - Em desenvolvimento")
                .navigationTitle("Configurações")
        }
    }
}