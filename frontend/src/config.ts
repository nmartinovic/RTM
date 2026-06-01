const DEFAULT_API_BASE_URL = 'http://localhost:8000';

const trimTrailingSlash = (value: string) => value.replace(/\/$/, '');

const configuredApiBaseUrl = import.meta.env?.VITE_API_BASE_URL?.trim();

export const apiBaseUrl = trimTrailingSlash(
  configuredApiBaseUrl || DEFAULT_API_BASE_URL,
);
