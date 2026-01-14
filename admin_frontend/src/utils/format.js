/**
 * Utility functions for formatting numbers, dates, etc.
 */

export const formatSats = (sats) => {
  return new Intl.NumberFormat().format(sats);
};

export const formatBTC = (btc) => {
  return btc.toFixed(8);
};

export const formatUSD = (usd) => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(usd);
};

export const formatPercent = (percent) => {
  return `${percent.toFixed(2)}%`;
};

export const formatDate = (dateString) => {
  return new Date(dateString).toLocaleString();
};

export const formatDateShort = (dateString) => {
  return new Date(dateString).toLocaleDateString();
};

export const satsToBTC = (sats) => {
  return sats / 100000000;
};
