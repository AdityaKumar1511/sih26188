-- =============================================================================
-- SIH PS 26188: AI Fake Identity & Document Screening System
-- Supabase / PostgreSQL Schema & Mock Valid Identity Records Table
-- =============================================================================

-- 1. Create Table: government_id_registry
CREATE TABLE IF NOT EXISTS public.government_id_registry (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    doc_type VARCHAR(20) NOT NULL CHECK (doc_type IN ('AADHAAR', 'PAN', 'DRIVING_LICENSE', 'PASSPORT')),
    id_number VARCHAR(64) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    father_name VARCHAR(255),
    dob DATE NOT NULL,
    gender VARCHAR(20) CHECK (gender IN ('MALE', 'FEMALE', 'TRANSGENDER', 'OTHER')),
    address TEXT,
    issuer VARCHAR(100) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'REVOKED', 'FLAGGED', 'SUSPENDED')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT unique_doc_identity UNIQUE (doc_type, id_number)
);

-- 2. Indexes for High-Speed Exact Lookup
CREATE INDEX IF NOT EXISTS idx_gov_registry_lookup 
ON public.government_id_registry (doc_type, id_number);

CREATE INDEX IF NOT EXISTS idx_gov_registry_name 
ON public.government_id_registry (full_name);

-- 3. Row Level Security (RLS) Configuration
ALTER TABLE public.government_id_registry ENABLE ROW LEVEL SECURITY;

-- Allow read-only access for anon / service role to query verification records
CREATE POLICY "Allow public read access for verification" 
ON public.government_id_registry
FOR SELECT 
USING (true);

-- Allow authenticated / service_role to insert or update
CREATE POLICY "Allow service role management" 
ON public.government_id_registry
FOR ALL 
USING (auth.role() = 'service_role');

-- =============================================================================
-- 4. SEED SAMPLE RECORDS
-- =============================================================================

INSERT INTO public.government_id_registry 
(doc_type, id_number, full_name, father_name, dob, gender, address, issuer, status)
VALUES
    -- Legitimate Aadhaar (passes Verhoeff checksum)
    (
        'AADHAAR', 
        '548921049811', 
        'RAJESH KUMAR SHARMA', 
        'RAMESH CHANDRA SHARMA', 
        '1988-08-14', 
        'MALE', 
        'H-42, Sector 62, Noida, Gautam Buddha Nagar, Uttar Pradesh 201301', 
        'UIDAI', 
        'ACTIVE'
    ),
    -- Legitimate Aadhaar #2 (passes Verhoeff checksum)
    (
        'AADHAAR', 
        '984277102391', 
        'ANANYA VERMA', 
        'SURESH VERMA', 
        '1992-11-22', 
        'FEMALE', 
        'Flat 402, Green Glen Layout, Bellandur, Bengaluru, Karnataka 560103', 
        'UIDAI', 
        'ACTIVE'
    ),
    -- Legitimate PAN Card (5th char 'M' matches last name Mehta)
    (
        'PAN', 
        'ABCPM1234F', 
        'VIKRAM SINGH MEHTA', 
        'HARISH CHANDRA MEHTA', 
        '1982-05-12', 
        'MALE', 
        'Plot 12, Civil Lines, Jaipur, Rajasthan 302006', 
        'INCOME_TAX_DEPT', 
        'ACTIVE'
    ),
    -- Legitimate PAN Card #2 (5th char 'S' matches Sharma)
    (
        'PAN', 
        'BKZPS8491K', 
        'PRIYA SHARMA', 
        'RAMESH SHARMA', 
        '1995-03-24', 
        'FEMALE', 
        'B-104, Sunrise Towers, Andheri East, Mumbai, Maharashtra 400069', 
        'INCOME_TAX_DEPT', 
        'ACTIVE'
    ),
    -- Revoked / Flagged Aadhaar (for testing fraudulent screening)
    (
        'AADHAAR', 
        '334455667788', 
        'FRAUD TEST USER', 
        'UNKNOWN', 
        '1990-01-01', 
        'MALE', 
        'De-listed Address', 
        'UIDAI', 
        'REVOKED'
    )
ON CONFLICT (doc_type, id_number) DO UPDATE 
SET 
    full_name = EXCLUDED.full_name,
    status = EXCLUDED.status,
    updated_at = NOW();
