import { api } from '@/lib/api';

import {
  SeriesFilter,
  SeriesOrder,
  SeriesOverviewPage,
} from '@/lib/types';


/**
 * 
 * @param {number} page 
 * @param {number} size 
 * @param {SeriesOrder} orderBy 
 * @param {SeriesFilter} filter 
 * @returns {Promise<SeriesOverviewPage[]>}
 */
export const getAllSeries = async (
  page = 1, size = 10, orderBy = 'name', filter = null,
) => {
  try {
    const response = await api.get('/series/all', {
      params: {
        page,
        size,
        orderBy,
        filter,
      },
    });
    return response.data;
  } catch (error) {
    console.error(error.response?.data?.detail || 'Error fetching daily balances:', error);
    throw error;
  }
};
