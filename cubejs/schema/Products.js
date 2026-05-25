cube(`Products`, {
  sql: `
    SELECT
      p.product_id,
      p.product_name,
      p.unit_price,
      p.units_in_stock,
      c.category_name
    FROM products p
    JOIN categories c ON p.category_id = c.category_id
  `,

  measures: {
    count: {
      type: `count`,
      description: `Total number of products`
    },
    avgPrice: {
      sql: `unit_price`,
      type: `avg`,
      format: `currency`,
      description: `Average unit price`
    },
    totalStock: {
      sql: `units_in_stock`,
      type: `sum`,
      description: `Total units in stock`
    },
    outOfStockCount: {
      sql: `CASE WHEN units_in_stock = 0 THEN 1 ELSE 0 END`,
      type: `sum`,
      description: `Number of products with zero stock`
    }
  },

  dimensions: {
    productId: {
      sql: `product_id`,
      type: `number`,
      primaryKey: true
    },
    productName: {
      sql: `product_name`,
      type: `string`
    },
    category: {
      sql: `category_name`,
      type: `string`,
      description: `Product category`
    },
    unitPrice: {
      sql: `unit_price`,
      type: `number`
    }
  }
});
