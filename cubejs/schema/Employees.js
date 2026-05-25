cube(`Employees`, {
  sql: `
    SELECT
      employee_id,
      first_name,
      last_name,
      title,
      department,
      salary,
      RANK() OVER (PARTITION BY department ORDER BY salary DESC) AS salary_rank,
      MAX(salary) OVER (PARTITION BY department) AS max_salary_in_dept,
      AVG(salary) OVER (PARTITION BY department) AS avg_salary_in_dept
    FROM employees
  `,

  measures: {
    count: {
      type: `count`,
      description: `Total number of employees`
    },
    avgSalary: {
      sql: `salary`,
      type: `avg`,
      format: `currency`,
      description: `Average salary`
    },
    maxSalary: {
      sql: `salary`,
      type: `max`,
      format: `currency`,
      description: `Highest salary`
    },
    totalPayroll: {
      sql: `salary`,
      type: `sum`,
      format: `currency`,
      description: `Total payroll cost`
    }
  },

  dimensions: {
    employeeId: {
      sql: `employee_id`,
      type: `number`,
      primaryKey: true
    },
    fullName: {
      sql: `first_name || ' ' || last_name`,
      type: `string`
    },
    title: {
      sql: `title`,
      type: `string`
    },
    department: {
      sql: `department`,
      type: `string`,
      description: `Department the employee belongs to`
    },
    salary: {
      sql: `salary`,
      type: `number`
    },
    salaryRank: {
      sql: `salary_rank`,
      type: `number`,
      description: `Rank within department by salary (1 = highest)`
    },
    maxSalaryInDept: {
      sql: `max_salary_in_dept`,
      type: `number`,
      description: `Highest salary in the same department`
    },
    avgSalaryInDept: {
      sql: `avg_salary_in_dept`,
      type: `number`,
      description: `Average salary in the same department`
    }
  }
});
