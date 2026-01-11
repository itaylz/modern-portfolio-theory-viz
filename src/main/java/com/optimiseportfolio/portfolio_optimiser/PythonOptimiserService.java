package com.optimiseportfolio.portfolio_optimiser;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.springframework.http.HttpHeaders;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpEntity;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

@Service
public class PythonOptimiserService {

    String pythonHost = System.getenv("PYTHON_HOST") != null ? System.getenv("PYTHON_HOST") : "localhost";
    private final String PYTHON_API_URL = "http://" + pythonHost + ":8000/optimize";;
    private final RestTemplate restTemplate;

    //start rest service 
    @Autowired
    public PythonOptimiserService(RestTemplate restTemplate){
        this.restTemplate = restTemplate;
    }

    public Map<String, Object> runOptimiser(List<String> tickers, String start, String end) {
        try {
            // 1. Prepare Request Body
            Map<String, Object> requestBody = new HashMap<>();
            requestBody.put("tickers", tickers);
            requestBody.put("start", start);
            requestBody.put("end", end);

            // 2. Set Headers
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);

            HttpEntity<Map<String, Object>> requestEntity = new HttpEntity<>(requestBody, headers);

            // 3. Make the call safely
            // "exchange" allows us to pass a ParameterizedTypeReference, which tells 
            // the compiler EXACTLY what kind of Map we expect (String keys, Object values).
            ResponseEntity<Map<String, Object>> responseEntity = restTemplate.exchange(
                PYTHON_API_URL,
                HttpMethod.POST,
                requestEntity,
                new ParameterizedTypeReference<Map<String, Object>>() {}
            );

            return responseEntity.getBody();

        } catch (Exception e) {
            Map<String, Object> errorResult = new HashMap<>();
            errorResult.put("error", "Failed to connect to Python Service");
            errorResult.put("details", e.getMessage());
            return errorResult;
        }
    }
}


