package com.acme.order;

import org.springframework.web.bind.annotation.*;
import org.springframework.kafka.core.KafkaTemplate;

@RestController
@RequestMapping("/api/orders")
public class OrderController {

    @PostMapping("/checkout")
    public OrderResponse checkout(@RequestBody CheckoutRequest req) {
        return orderService.processCheckout(req);
    }

    @GetMapping("/{id}")
    public Order getOrder(@PathVariable String id) {
        return orderService.findById(id);
    }

    @DeleteMapping("/{id}")
    public void cancelOrder(@PathVariable String id) {
        orderService.cancel(id);
    }
}