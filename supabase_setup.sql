-- Run this script in your Supabase SQL Editor to create the necessary tables.

-- 1. Table for tracking user searches
CREATE TABLE IF NOT EXISTS public.user_queries (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    exam_name TEXT NOT NULL,
    user_id TEXT DEFAULT 'anonymous',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 2. Table for caching scraped exam resources
CREATE TABLE IF NOT EXISTS public.exam_resources (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    exam_name TEXT NOT NULL UNIQUE,
    syllabus JSONB DEFAULT '[]'::jsonb,
    previous_papers JSONB DEFAULT '[]'::jsonb,
    important_topics JSONB DEFAULT '[]'::jsonb,
    resources JSONB DEFAULT '[]'::jsonb,
    youtube_lectures JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 3. Table for saving AI-generated study plans
CREATE TABLE IF NOT EXISTS public.study_plans (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    exam_name TEXT NOT NULL UNIQUE,
    plan_data JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Note: The UNIQUE constraints on 'exam_name' in the last two tables 
-- are required for the agent's "upsert" commands to function properly.
