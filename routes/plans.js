const express = require('express');
const router = express.Router();
const plans = require('../data/plans.json');

router.get('/', (req, res) => {
  res.render('plans/index', { title: 'Plans', activePage: 'plans', plans });
});

router.get('/:id', (req, res) => {
  const plan = plans.find(p => p.id === req.params.id);
  if (!plan) return res.redirect('/plans');
  res.render('plans/detail', { title: plan.name + ' Plan', activePage: 'plans', plan, plans });
});

module.exports = router;
