package com.optimiseportfolio.portfolio_optimiser;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import java.util.Arrays;
import java.util.List;
import java.util.Map;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.client.RestTemplate;

@ExtendWith(MockitoExtension.class)
class PythonOptimiserServiceTest {

    @Mock
    private RestTemplate restTemplate;

    @InjectMocks
    private PythonOptimiserService pythonOptimiserService;

    @Test
    void testRunOptimiser_Success() {
        // Arrange
        List<String> tickers = Arrays.asList("AAPL", "MSFT");
        String start = "2023-01-01";
        String end = "2023-12-31";

        Map<String, Object> mockResponseMap = Map.of("result", "success");
        ResponseEntity<Map<String, Object>> responseEntity = new ResponseEntity<>(mockResponseMap, HttpStatus.OK);

        when(restTemplate.exchange(
            any(String.class), 
            eq(HttpMethod.POST), 
            any(HttpEntity.class), 
            any(ParameterizedTypeReference.class))
        ).thenReturn(responseEntity);

        // Act
        Map<String, Object> result = pythonOptimiserService.runOptimiser(tickers, start, end);

        // Assert
        assertEquals("success", result.get("result"));
        
        // Verify that restTemplate was called with the correct URL/Method
        verify(restTemplate).exchange(
            any(String.class), 
            eq(HttpMethod.POST), 
            any(HttpEntity.class), 
            any(ParameterizedTypeReference.class)
        );
    }

    @Test
    void testRunOptimiser_Failure() {
        // Arrange
        List<String> tickers = Arrays.asList("BAD_TICKER");
        
        // Simulate an exception (e.g., Python service is down)
        when(restTemplate.exchange(
            any(String.class), 
            eq(HttpMethod.POST), 
            any(HttpEntity.class), 
            any(ParameterizedTypeReference.class))
        ).thenThrow(new RuntimeException("Connection Refused"));

        // Act
        Map<String, Object> result = pythonOptimiserService.runOptimiser(tickers, "2023-01-01", "2023-12-31");

        // Assert
        assertTrue(result.containsKey("error"));
        assertEquals("Failed to connect to Python Service", result.get("error"));
    }
}