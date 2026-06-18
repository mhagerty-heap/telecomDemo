const express = require('express');
const router = express.Router();

router.get('/', (req, res) => {
  res.render('stores', { title: 'Find a Store', activePage: 'stores' });
});

module.exports = router;
