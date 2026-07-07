export function onlyDigits(value: string, maxLength = 6): string {
  return value.replace(/\D/g, "").slice(0, maxLength);
}
