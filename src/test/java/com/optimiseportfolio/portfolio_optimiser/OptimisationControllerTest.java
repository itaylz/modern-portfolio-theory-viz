package com.optimiseportfolio.portfolio_optimiser;

import static org.mockito.ArgumentMatchers.anyList;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.content;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import java.util.Arrays;
import java.util.HashMap;
import java.util.Map;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

import com.fasterxml.jackson.databind.ObjectMapper;

@WebMvcTest(OptimisationController.class)
class OptimisationControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private PythonOptimiserService pythonService;

    @Autowired
    private ObjectMapper objectMapper;

    @Test
    void testOptimisePortfolio_Success() throws Exception {
        // 1. Prepare Request Data
        Map<String, Object> requestBody = new HashMap<>();
        requestBody.put("tickers", Arrays.asList("AAPL", "GOOG"));
        requestBody.put("start", "2024-01-01");
        requestBody.put("end", "2025-01-01");

        // 2. Prepare Mock Response from Service
        Map<String, Object> mockServiceResponse = new HashMap<>();
        mockServiceResponse.put("status", "optimised");
        mockServiceResponse.put("weights", Map.of("AAPL", 0.5, "GOOG", 0.5));

        // Note: Using anyList() fixed the type safety warning
        when(pythonService.runOptimiser(anyList(), anyString(), anyString()))
                .thenReturn(mockServiceResponse);

        // 3. Perform POST Request and Verify
        mockMvc.perform(post("/api/optimise")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(requestBody)))
                .andExpect(status().isOk())
                .andExpect(content().contentType(MediaType.APPLICATION_JSON))
                .andExpect(jsonPath("$.status").value("optimised"))
                .andExpect(jsonPath("$.weights.AAPL").value(0.5));
    }
}