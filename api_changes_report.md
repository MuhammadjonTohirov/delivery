# API Changes Report

This report summarizes the recent enhancements to the Order Details API and clarifications regarding the Restaurant List API.

## 1. Order Details API Enhancement

*   **Endpoint:** `GET /orders/{order_id}/`
    *   This is the standard retrieve action for the `OrderViewSet`. The exact URL depends on the router configuration in `urls.py`, but typically defaults to this pattern.
*   **Description:** This API now returns a comprehensive, nested JSON structure for order details, providing a richer set of information for a single order.
*   **Key Changes:**
    *   The response for fetching a single order has been significantly expanded. It now includes detailed, nested objects for:
        *   `status`: Contains the `current` status of the order and a `timeline` of all `OrderStatusEventSerializer` (status, timestamp, completed flag).
        *   `restaurant`: Detailed information about the restaurant via `RestaurantDetailSerializer` (`id`, `name`, placeholder `cuisine`, calculated `rating`, placeholder `deliveryTime`).
        *   `customer`: Detailed information about the customer via `CustomerDetailSerializer` (`id`, `name`, `phone`).
        *   `deliveryAddress`: Detailed delivery address information via `DeliveryAddressSerializer` (placeholders for `street`, `city`, `state`, `zipCode`, `country` from the single `delivery_address` field, `fullAddress`, nested `coordinates` from `delivery_lat`/`lng`, and placeholder `mapImageUrl`).
        *   `items`: A list of ordered items, with each item using `OrderItemDetailSerializer`. This includes `id` (OrderItem ID), `name` (MenuItem name), `description` (MenuItem description), `quantity`, `unitPrice` (OrderItem unit price), calculated `totalPrice`, `imageUrl` (MenuItem image), `category` (MenuItem category name), placeholder `customizations`, and `specialInstructions` (OrderItem notes).
        *   `pricing`: A breakdown of pricing via `PricingDetailSerializer` (calculated `subtotal` from item subtotals, `deliveryFee`, placeholders for `serviceFee`, `tax`, `tip`, `discount` from Order, and `total` from Order).
        *   `payment`: Placeholder payment details via `PaymentDetailSerializer` (placeholder `method`, `cardLast4`, `cardType`, `transactionId`, `status`).
        *   `delivery`: Delivery-related information via `DeliveryDetailSerializer` (placeholder `type`, `estimatedTime` from Order, placeholder `actualDeliveryTime`, nested `driver` details (nullable), and `instructions` from Order notes).
        *   `timestamps`: Key order timestamps via `OrderTimestampDetailSerializer` (`ordered` for 'PLACED' status, `confirmed` for 'CONFIRMED' status, `delivered` for 'DELIVERED' status).
    *   Many fields that were not directly available in the database models have been included as placeholders (e.g., `restaurant.cuisine`, `restaurant.deliveryTime`, parsed address components in `deliveryAddress` like `street`/`city`/`state`/`zipCode`/`country`, `deliveryAddress.mapImageUrl`, `orderItem.customizations`, `pricing.serviceFee`/`tax`/`tip`, all fields in `payment`, `delivery.type`, `delivery.actualDeliveryTime`, `driver.rating`). These will either require backend model/logic updates to populate accurately or should be handled as display-only with placeholder/default values in the UI.
    *   The `metadata` field has been excluded from the order details response as requested.
*   **Action:**
    *   The UI team should adapt the order details view to consume this new, richer, and more nested JSON structure.
    *   Be mindful of the placeholder fields and discuss with the backend team which of these will be fully implemented versus those that will remain static placeholders.

## 2. Restaurant List API Consolidation

*   **Endpoint:** `GET /restaurants/` (typically, or `/restaurants/list/` if explicitly configured by a custom router, but standard ViewSet list routes are usually at the base path). The `RestaurantViewSet` also includes a specific search action at `GET /restaurants/search/?q={query}`.
*   **Description:** This is confirmed as the primary and sole API for fetching a list of restaurants. The `RestaurantViewSet` provides comprehensive listing, filtering (e.g., `is_open`), and searching capabilities.
*   **Key Changes:**
    *   No endpoints were removed. The investigation confirmed that the existing `RestaurantViewSet` (accessible via `/restaurants/` and its sub-paths like `/restaurants/search/`) is the correct and most comprehensive API for restaurant listings.
    *   The endpoint supports filtering by fields like `is_open` and full-text search on `name`, `address`, and `description` via query parameters (e.g., `/restaurants/?is_open=true`, `/restaurants/search/?q=pizza`). Ordering is also supported.
*   **Action:**
    *   The UI team should continue using the `GET /restaurants/` endpoint (and its search variant `GET /restaurants/search/`) for displaying restaurant lists and implementing search/filter functionalities.

## 3. Order Item Details

*   **Context:** This is part of the **Order Details API Enhancement** (`GET /orders/{order_id}/`).
*   **Description:** As mentioned in section 1, each item within the `items` array of the order detail response (`OrderDetailSerializer`) now uses `OrderItemDetailSerializer`.
*   **Key Information per Item:**
    *   `id`: The ID of the `OrderItem` itself.
    *   `name`: Name of the `MenuItem`.
    *   `description`: Description of the `MenuItem`.
    *   `quantity`: Quantity ordered.
    *   `unitPrice`: Price per unit for this specific order item (could differ from current menu item price if it changed).
    *   `totalPrice`: Calculated as `quantity * unitPrice`.
    *   `imageUrl`: Image of the `MenuItem`.
    *   `category`: Name of the `MenuCategory` for the item.
    *   `customizations`: Placeholder field (currently returns an empty list).
    *   `specialInstructions`: Notes added by the customer for this specific item.

## 4. General Notes

*   **No API Removals:**
    *   No order detail APIs were removed. The existing `OrderViewSet`'s `retrieve` action was enhanced to return the new `OrderDetailSerializer`.
    *   No restaurant list APIs were removed, as the primary endpoint provided by `RestaurantViewSet` was found to be unique, appropriate, and feature-rich.
*   **Metadata Exclusion:** The `metadata` field, if it existed previously or was a concern, has been explicitly excluded from the new `OrderDetailSerializer` response.
*   **Placeholder Fields:** A significant number of fields in the new `OrderDetailSerializer` are placeholders due to lack of direct corresponding data in the current database models or business logic. These are clearly marked in the serializer definitions (e.g., returning `None` or a static string like "To be implemented"). These will require further backend work to become dynamic or will be acknowledged as static placeholders.

This report should provide clarity to the UI team on how to adapt to the updated API responses.
