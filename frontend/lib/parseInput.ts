import type { FeatureInput, IsoDateString } from "./types";
import { DEFAULT_FEATURE_INPUT } from "./features";

/**
 * Parse a .txt file content into FeatureInput.
 * Expected format: key: value (one per line)
 * Supports both PascalCase and snake_case keys.
 */
export function parseTxtInput(fileContent: string): Partial<FeatureInput> {
  const result: Partial<FeatureInput> = { ...DEFAULT_FEATURE_INPUT };
  const lines = fileContent.split("\n");

  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith("#")) continue; // Skip empty lines and comments

    const colonIndex = trimmed.indexOf(":");
    if (colonIndex === -1) continue;

    const key = trimmed.substring(0, colonIndex).trim();
    const value = trimmed.substring(colonIndex + 1).trim();

    if (!key || !value) continue;

    // Convert snake_case to PascalCase (optional for user convenience)
    const pascalKey = convertKeyFormat(key) as keyof FeatureInput;

    // Try to assign the value, converting to appropriate type
    try {
      (result as Record<string, any>)[pascalKey] = convertValue(
        value,
        getValueType(pascalKey)
      );
    } catch (e) {
      console.warn(`Failed to parse field ${key}: ${e}`);
    }
  }

  return result;
}

/**
 * Convert snake_case or lowercase key to PascalCase.
 * Examples: "name" -> "Name", "release_date" -> "ReleaseDate"
 */
function convertKeyFormat(key: string): string {
  // If already PascalCase, return as is
  if (/^[A-Z][a-zA-Z0-9]*$/.test(key)) {
    return key;
  }

  // Convert snake_case to PascalCase
  return key
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
    .join("");
}

/**
 * Determine the expected type for a given feature key.
 */
function getValueType(key: keyof FeatureInput): "string" | "number" | "boolean" | "date" {
  // Boolean fields
  if (
    key.startsWith("Is") ||
    key.startsWith("Has") ||
    key.startsWith("Avail") ||
    key.startsWith("Support") ||
    key.startsWith("Platform") ||
    key.startsWith("PCReqs") ||
    key.startsWith("LinuxReqs") ||
    key.startsWith("MacReqs") ||
    key.startsWith("Category") ||
    key.startsWith("Genre")
  ) {
    return "boolean";
  }

  // Date field
  if (key === "ReleaseDate") {
    return "date";
  }

  // Numeric fields - check if the key suggests a number
  if (
    key.includes("Count") ||
    key.includes("Price") ||
    key.includes("Age") ||
    key.includes("Variance") ||
    key.includes("Estimate") ||
    key.includes("Owner") ||
    key.includes("Players") ||
    key.includes("Year") ||
    key.includes("Month") ||
    key.includes("Metacritic")
  ) {
    return "number";
  }

  // Default to string
  return "string";
}

/**
 * Convert a string value to the appropriate type.
 */
function convertValue(
  value: string,
  type: "string" | "number" | "boolean" | "date"
): string | number | boolean {
  switch (type) {
    case "boolean":
      return (
        value.toLowerCase() === "true" ||
        value.toLowerCase() === "yes" ||
        value === "1"
      );
    case "number":
      return parseFloat(value);
    case "date":
      // Validate ISO date format
      if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) {
        throw new Error(
          `Invalid date format. Expected YYYY-MM-DD, got ${value}`
        );
      }
      return value as IsoDateString;
    case "string":
    default:
      return value;
  }
}
