# ── Build stage ──────────────────────────────────────────────────────────────
FROM maven:3.9.6-eclipse-temurin-8 AS builder
WORKDIR /app
COPY pom.xml .
RUN mvn dependency:go-offline -B -q
COPY src ./src
RUN mvn package -DskipTests -B -q

# ── Run stage ─────────────────────────────────────────────────────────────────
FROM eclipse-temurin:8-jre
WORKDIR /app
COPY --from=builder /app/target/estacionamento.jar estacionamento.jar
EXPOSE 8080
CMD ["java", "-jar", "estacionamento.jar"]
