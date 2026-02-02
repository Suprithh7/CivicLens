/**
 * Custom hook for pagination logic
 * Manages pagination state and calculations
 */

export function usePagination(total, itemsPerPage) {
  const totalPages = Math.ceil(total / itemsPerPage);

  const getPageNumbers = (currentPage) => {
    const pages = [];

    for (let i = 1; i <= totalPages; i++) {
      // Show first, last, current, and adjacent pages
      if (
        i === 1 ||
        i === totalPages ||
        (i >= currentPage - 1 && i <= currentPage + 1)
      ) {
        pages.push(i);
      } else if (i === currentPage - 2 || i === currentPage + 2) {
        pages.push('...');
      }
    }

    // Remove consecutive ellipses
    return pages.filter((page, index, array) => {
      if (page !== '...') return true;
      return array[index - 1] !== '...';
    });
  };

  return {
    totalPages,
    getPageNumbers,
  };
}
