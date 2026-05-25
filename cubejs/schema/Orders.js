cube(`Orders`, {
  sql: `
    SELECT
      o.order_id,
      o.customer_id,
      o.employee_id,
      o.order_date,
      o.ship_country,
      o.freight,
      od.product_id,
      od.unit_price,
      od.quantity,
      od.discount
    FROM orders o
    JOIN order_details od ON o.order_id = od.order_id
  `,

  measures: {
    count: {
      type: `count`,
      description: `Total number of order line items`
    },
    orderCount: {
      sql: `order_id`,
      type: `countDistinct`,
      description: `Total number of distinct orders`
    },
    totalRevenue: {
      sql: `unit_price * quantity * (1 - discount)`,
      type: `sum`,
      format: `currency`,
      description: `Total revenue after discounts`
    },
    avgOrderValue: {
      sql: `unit_price * quantity * (1 - discount)`,
      type: `avg`,
      format: `currency`,
      description: `Average order line item value`
    },
    totalFreight: {
      sql: `freight`,
      type: `sum`,
      format: `currency`,
      description: `Total freight / shipping cost`
    }
  },

  dimensions: {
    orderId: {
      sql: `order_id`,
      type: `number`,
      primaryKey: true
    },
    customerId: {
      sql: `customer_id`,
      type: `string`
    },
    employeeId: {
      sql: `employee_id`,
      type: `number`
    },
    shipCountry: {
      sql: `ship_country`,
      type: `string`,
      description: `Country the order was shipped to`
    },
    orderDate: {
      sql: `order_date`,
      type: `time`,
      description: `Date the order was placed`
    }
  }
});
