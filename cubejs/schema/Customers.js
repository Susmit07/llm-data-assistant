cube(`Customers`, {
  sql: `SELECT * FROM customers`,

  measures: {
    count: {
      type: `count`,
      description: `Total number of customers`
    }
  },

  dimensions: {
    customerId: {
      sql: `customer_id`,
      type: `string`,
      primaryKey: true
    },
    companyName: {
      sql: `company_name`,
      type: `string`
    },
    contactName: {
      sql: `contact_name`,
      type: `string`
    },
    city: {
      sql: `city`,
      type: `string`
    },
    country: {
      sql: `country`,
      type: `string`,
      description: `Country the customer is based in`
    }
  }
});
