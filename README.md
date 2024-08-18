# INTRODUCTION
I have developed an advanced data engineering project centered around the real-time processing and management of large-scale real estate data. The project begins by leveraging sophisticated web crawling and scraping techniques to extract comprehensive property data from Zoopla, a prominent platform for house sales. This data is then seamlessly streamed into a robust Kafka cluster, with the entire workflow meticulously orchestrated and scheduled through Apache Airflow to ensure efficiency and reliability.

The second phase of the project focuses on real-time data processing using a distributed Spark cluster. The Spark cluster consumes the data from Kafka, applies various transformations and processing steps to enrich the dataset, and subsequently stores the refined data into a high-performance Cassandra DB cluster. This architecture not only ensures scalable data handling but also supports complex, real-time analytics and decision-making for real estate insights.


# ARCHITECTURE
![image](https://github.com/user-attachments/assets/d6d0ee8b-1706-4679-ac08-c486a64ede69)


# TOOL AND TECHNOLY
- Python (Selenium, Beautiful Soup, Undecteced-Chromedriver)
- Apache Spark
- Apache Kafka, Apache Zookeeper
- Apache Airflow
- PostgresSQL, Apache Cassandra

# WORK FLOW
- Crawled and scraped comprehensive real estate data from Zoopla, focusing on properties in London.
- Utilized a Large Language Model (LLM) based on GEMINI to assist in data extraction.
- Streamed the data into a Kafka cluster for real-time processing.
- Scheduled and managed web scraping and data streaming tasks using Apache Airflow.
- Processed the streamed data from Kafka using a Spark cluster, then stored it in a Cassandra database.
- Deployed the entire system using Docker for scalability and ease of management.
