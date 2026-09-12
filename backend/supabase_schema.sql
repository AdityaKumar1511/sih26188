-- ==============================================================================
-- Supabase Schema for Sentinel PS26188 Government ID Registry
-- ==============================================================================

CREATE TABLE IF NOT EXISTS public.government_id_registry (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    doc_type TEXT NOT NULL,
    id_number TEXT NOT NULL,
    full_name TEXT NOT NULL,
    father_name TEXT,
    dob TEXT NOT NULL,
    gender TEXT,
    status TEXT NOT NULL DEFAULT 'ACTIVE',
    issuer TEXT NOT NULL DEFAULT 'GOVERNMENT_OF_INDIA',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Index for fast lookup by doc_type and id_number
CREATE INDEX IF NOT EXISTS idx_gov_id ON public.government_id_registry (doc_type, id_number);

-- Enable Row Level Security (RLS)
ALTER TABLE public.government_id_registry ENABLE ROW LEVEL SECURITY;

-- Allow anonymous read access for document screening verification
CREATE POLICY "Allow public read on government_id_registry" 
ON public.government_id_registry 
FOR SELECT 
USING (true);

-- Pre-seed test records
INSERT INTO public.government_id_registry (doc_type, id_number, full_name, dob, gender, status, issuer)
VALUES 
    ('AADHAAR', '548921049811', 'RAJESH KUMAR SHARMA', '1988-08-14', 'MALE', 'ACTIVE', 'UIDAI'),
    ('AADHAAR', '984277102391', 'ANANYA VERMA', '1992-11-22', 'FEMALE', 'ACTIVE', 'UIDAI'),
    ('AADHAAR', '266348132551', 'YUVRAJ ATRI', '2008-03-04', 'MALE', 'ACTIVE', 'UIDAI'),
    ('PAN', 'ABCPM1234F', 'VIKRAM SINGH MEHTA', '1982-05-12', 'MALE', 'ACTIVE', 'INCOME_TAX_DEPT'),
    ('PAN', 'BKZPR8491K', 'PRIYA SHARMA', '1995-03-24', 'FEMALE', 'ACTIVE', 'INCOME_TAX_DEPT')
ON CONFLICT DO NOTHING;
