const trimTrailingSlash = (value: string) => value.replace(/\/$/, '');

export const apiBaseUrl = trimTrailingSlash(
  import.meta.env?.VITE_API_BASE_URL ?? 'http://localhost:8000',
);
