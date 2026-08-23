CREATE TABLE IF NOT EXISTS users (
    id BIGSERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    phone VARCHAR(30),
    profile_image TEXT,
    is_verified BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS properties (
    id BIGSERIAL PRIMARY KEY,
    owner_id BIGINT NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    property_type VARCHAR(50) NOT NULL,
    price NUMERIC(12,2) NOT NULL,
    city VARCHAR(100) NOT NULL,
    district VARCHAR(150),
    address TEXT,
    latitude NUMERIC(10,7),
    longitude NUMERIC(10,7),
    surface NUMERIC(10,2),
    bedrooms INTEGER NOT NULL DEFAULT 0,
    bathrooms INTEGER NOT NULL DEFAULT 0,
    furnished BOOLEAN NOT NULL DEFAULT FALSE,
    parking BOOLEAN NOT NULL DEFAULT FALSE,
    elevator BOOLEAN NOT NULL DEFAULT FALSE,
    air_conditioning BOOLEAN NOT NULL DEFAULT FALSE,
    status VARCHAR(30) NOT NULL DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_properties_owner
        FOREIGN KEY (owner_id)
        REFERENCES users(id)
        ON DELETE CASCADE,
    CONSTRAINT properties_price_positive
        CHECK (price >= 0),
    CONSTRAINT properties_surface_positive
        CHECK (surface IS NULL OR surface > 0),
    CONSTRAINT properties_bedrooms_positive
        CHECK (bedrooms >= 0),
    CONSTRAINT properties_bathrooms_positive
        CHECK (bathrooms >= 0),
    CONSTRAINT properties_type_check
        CHECK (
            property_type IN (
                'Appartement',
                'Maison',
                'Villa',
                'Studio',
                'Commerce',
                'Bureau',
                'Terrain',
                'Autre'
            )
        ),
    CONSTRAINT properties_status_check
        CHECK (
            status IN (
                'active',
                'rented',
                'pending',
                'hidden'
            )
        )
);
CREATE INDEX IF NOT EXISTS idx_properties_owner
ON properties(owner_id);
CREATE INDEX IF NOT EXISTS idx_properties_city
ON properties(city);
CREATE INDEX IF NOT EXISTS idx_properties_type
ON properties(property_type);
CREATE INDEX IF NOT EXISTS idx_properties_price
ON properties(price);
CREATE INDEX IF NOT EXISTS idx_properties_status
ON properties(status);
CREATE INDEX IF NOT EXISTS idx_properties_created
ON properties(created_at DESC);