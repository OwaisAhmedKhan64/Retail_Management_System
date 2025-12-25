CREATE TABLE `restocks` (
  `restock_id` int NOT NULL AUTO_INCREMENT,
  `product_id` int NOT NULL,
  `quantity_added` int NOT NULL,
  `cost_price_at_restock` float DEFAULT NULL,
  `restock_date` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`restock_id`),
  KEY `product_id` (`product_id`),
  CONSTRAINT `restocks_ibfk_1` FOREIGN KEY (`product_id`) REFERENCES `products` (`product_id`)
)
INSERT INTO `restocks` VALUES (1,8,33,25,'2025-11-19 08:55:11'),(2,5,2,10,'2025-11-19 08:57:48'),(4,7,1000,3,'2025-11-19 09:04:23'),(5,11,100,85,'2025-11-19 23:01:56'),(6,52,3,40,'2025-11-21 08:22:03');