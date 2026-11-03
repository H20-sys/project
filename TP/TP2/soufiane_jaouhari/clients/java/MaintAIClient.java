// Client Java de l'API MaintAI : la même requête que la page web, curl.exe ou les tests.
//
// Lancement (Java 11+, sans compilation séparée), API démarrée avec --env-file .env :
//   PowerShell : $env:MAINTAI_API_KEY = "votre-cle" ; java clients\java\MaintAIClient.java
//   cmd        : set MAINTAI_API_KEY=votre-cle && java clients\java\MaintAIClient.java
//
// La clé est lue dans une variable d'environnement, jamais écrite dans le code.

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;

public class MaintAIClient {

    public static void main(String[] args) throws Exception {
        String url = System.getenv().getOrDefault("MAINTAI_URL", "http://localhost:8000");
        String key = System.getenv("MAINTAI_API_KEY");
        if (key == null || key.isBlank()) {
            // é = é : le message reste juste quel que soit l'encodage du fichier source
            System.err.println("Variable MAINTAI_API_KEY absente : définissez-la avec la clé de .env");
            System.exit(1);
        }

        // Le relevé, en JSON : les mêmes champs que SensorReading (schemas.py)
        String reading = """
                {"temperature_c": 72.5, "vibration_mm_s": 6.1, "load_pct": 85, "runtime_hours": 15000}
                """;

        HttpRequest request = HttpRequest.newBuilder(URI.create(url + "/v1/predict"))
                .header("Content-Type", "application/json")
                .header("X-API-Key", key) // la clé voyage dans un en-tête, jamais dans l'URL
                .POST(HttpRequest.BodyPublishers.ofString(reading))
                .build();

        // HTTP/1.1 : par défaut, Java tente de passer en HTTP/2 (en-tête Upgrade: h2c),
        // qu'uvicorn ne gère pas, et le corps de la requête se perd (422 « Field required »)
        HttpClient client = HttpClient.newBuilder()
                .version(HttpClient.Version.HTTP_1_1)
                .build();
        HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());

        // 200 : la prédiction ; 401 : clé ; 422 : relevé refusé ; 503 : modèle absent
        System.out.println("HTTP " + response.statusCode());
        System.out.println(response.body());
    }
}
