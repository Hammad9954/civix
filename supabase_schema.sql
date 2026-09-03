-- ============================================================
-- CivicSense / Civix — Supabase Database Migration (V4 Auth)
-- Run this in your Supabase SQL Editor:
-- https://supabase.com/dashboard/project/_/sql/new
-- ============================================================

-- 1. Create the public `profiles` table
--    Associates an authenticated Supabase user with a stable,
--    pseudonymous public reporter identifier (e.g. CIV-7F3A2).
--    NO email, NO name, and NO password is stored here.
CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    public_reporter_id TEXT UNIQUE NOT NULL,
    role TEXT NOT NULL DEFAULT 'citizen',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 2. Enable Row Level Security (RLS)
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

-- 3. RLS Policies
-- Users can view their own profile
CREATE POLICY "Users can view own profile" 
ON public.profiles 
FOR SELECT 
USING (auth.uid() = id);

-- Service role (used by Flask backend) can manage all profiles
CREATE POLICY "Service role full access on profiles"
ON public.profiles
FOR ALL
USING (true)
WITH CHECK (true);

-- 4. Function: Generate a unique, stable pseudonymous reporter ID (e.g. CIV-7F3A2)
CREATE OR REPLACE FUNCTION public.generate_reporter_id()
RETURNS TEXT AS $$
DECLARE
    new_id TEXT;
    done BOOLEAN;
BEGIN
    done := FALSE;
    WHILE NOT done LOOP
        -- Generates 'CIV-' followed by 5 uppercase hexadecimal characters
        new_id := 'CIV-' || UPPER(SUBSTRING(MD5(RANDOM()::TEXT || CLOCK_TIMESTAMP()::TEXT) FROM 1 FOR 5));
        -- Ensure uniqueness
        PERFORM 1 FROM public.profiles WHERE public_reporter_id = new_id;
        IF NOT FOUND THEN
            done := TRUE;
        END IF;
    END LOOP;
    RETURN new_id;
END;
$$ LANGUAGE plpgsql;

-- 5. Trigger Function: Automatically create profile when a new user signs up
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.profiles (id, public_reporter_id, role)
    VALUES (
        NEW.id,
        public.generate_reporter_id(),
        'citizen'
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 6. Attach trigger to auth.users table
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- ============================================================
-- 7. (Optional / Future) Reports table with user_id relationship
-- ============================================================
CREATE TABLE IF NOT EXISTS public.reports (
    id TEXT PRIMARY KEY,
    user_id UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
    reporter_id TEXT,
    issue_type TEXT NOT NULL,
    confirmed_category TEXT,
    description TEXT,
    image_filename TEXT,
    image_path TEXT,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    priority JSONB,
    status TEXT NOT NULL DEFAULT 'Reported',
    duplicates JSONB,
    spam JSONB,
    resolution JSONB,
    assignment JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE public.reports ENABLE ROW LEVEL SECURITY;

-- Allow public read of reports (or authenticated users only)
CREATE POLICY "Allow public read on reports" 
ON public.reports FOR SELECT USING (true);

-- Allow backend service role full access
CREATE POLICY "Service role full access on reports"
ON public.reports FOR ALL USING (true) WITH CHECK (true);
