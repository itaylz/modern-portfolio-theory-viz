package com.optimiseportfolio.portfolio_optimiser;

import java.util.List;
import java.util.Map;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.core.type.TypeReference;


@RestController
@RequestMapping("/api/optimise")
@CrossOrigin(origins = "*")
public class OptimisationController {

    
    private final PythonOptimiserService pythonService;

    @Autowired
    public OptimisationController(PythonOptimiserService pythonService) {
        this.pythonService = pythonService;
    }

    @PostMapping
    public ResponseEntity<Map<String, Object>> optimisePortfolio(@RequestBody Map<String, Object> request) {
        ObjectMapper mapper = new ObjectMapper();
        List<String> tickers = mapper.convertValue(request.get("tickers"), new TypeReference<List<String>>() {});
        String start = (String) request.getOrDefault("start", "2024-01-01");
        String end = (String) request.getOrDefault("end", "2025-01-01");

        Map<String, Object> result = pythonService.runOptimiser(tickers, start, end);

        return ResponseEntity.ok(result);
    }
}


