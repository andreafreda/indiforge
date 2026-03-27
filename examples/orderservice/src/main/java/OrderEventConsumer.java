package com.acme.order;

import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.stereotype.Component;

@Component
public class OrderEventConsumer {

    @KafkaListener(topics = "payment-events", groupId = "order-group")
    public void handlePaymentEvent(String event) {
        orderService.updateOrderStatus(event);
    }

    @KafkaListener(topics = "inventory-events", groupId = "order-group")
    public void handleInventoryEvent(String event) {
        orderService.checkInventory(event);
    }
}