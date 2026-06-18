const express = require('express');
const router = express.Router();
const plans = require('../data/plans.json');

router.get('/', (req, res) => {
  res.render('home', {
    title: 'Home',
    activePage: 'home',
    featuredPlans: plans.slice(0, 3)
  });
});

module.exports = router;
