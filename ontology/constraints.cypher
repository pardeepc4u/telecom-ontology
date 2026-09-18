// Uniqueness constraints derived from ontology/schema.yaml.
//
// Neo4j Community Edition supports uniqueness constraints but not property
// existence constraints (those require Enterprise) — required-field
// enforcement for now lives in the data generator and ingestion scripts,
// not the database. Run this file once against a fresh database before
// ingestion (Phase 3).

CREATE CONSTRAINT cell_tower_id IF NOT EXISTS FOR (n:CellTower) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT router_id IF NOT EXISTS FOR (n:Router) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT customer_id IF NOT EXISTS FOR (n:Customer) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT service_plan_id IF NOT EXISTS FOR (n:ServicePlan) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT ticket_id IF NOT EXISTS FOR (n:Ticket) REQUIRE n.id IS UNIQUE;
