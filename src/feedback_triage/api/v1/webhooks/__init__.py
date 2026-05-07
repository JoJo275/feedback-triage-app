"""Inbound provider-webhook routes.

Currently only Resend (PR 4.3). Each provider gets its own module so
signature-verification quirks (Standard Webhooks, HMAC, etc.) stay
local to the surface that actually receives them.
"""
