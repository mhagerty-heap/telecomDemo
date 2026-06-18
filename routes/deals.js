const express = require('express');
const router = express.Router();

router.get('/', (req, res) => {
  res.render('deals', { title: 'Deals & Promotions', activePage: 'deals' });
});

module.exports = router;
