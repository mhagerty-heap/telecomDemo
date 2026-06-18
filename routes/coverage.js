const express = require('express');
const router = express.Router();

router.get('/', (req, res) => {
  res.render('coverage', { title: 'Coverage Map', activePage: 'coverage' });
});

module.exports = router;
