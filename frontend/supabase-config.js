/**
 * Civic Sense — Supabase Client Configuration (Browser-Safe)
 *
 * This file initializes the Supabase JS client using ONLY the public
 * anon key. The service-role key is NEVER used here.
 *
 * IMPORTANT: Update SUPABASE_URL and SUPABASE_ANON_KEY below with
 * your Supabase project values from:
 * https://supabase.com/dashboard/project/_/settings/api
 */

// ── Supabase Configuration ──────────────────────────────────
// TODO: Replace these with your actual Supabase project values
const SUPABASE_URL = "https://dkywhcidmvbjezoiatwk.supabase.co";
const SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRreXdoY2lkbXZiamV6b2lhdHdrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODg0NDcxNTgsImV4cCI6MjEwNDAyMzE1OH0.AhRGpM9faFXTRYzIvR6JQbWD8-6HmD62vzooN4tm4Qo";

// ── Initialize Client ───────────────────────────────────────
let _supabaseClient = null;

function getSupabase() {
  if (_supabaseClient) return _supabaseClient;

  if (typeof supabase !== "undefined" && supabase.createClient) {
    _supabaseClient = supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
  } else {
    console.error("Supabase JS library not loaded. Include the CDN script before supabase-config.js");
  }

  return _supabaseClient;
}
