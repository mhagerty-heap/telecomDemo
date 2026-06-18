const express = require('express');
const router = express.Router();
const devices = require('../data/devices.json');

router.get('/', (req, res) => {
  res.render('devices/index', { title: 'Devices', activePage: 'devices', devices });
});

router.get('/:id', (req, res) => {
  const device = devices.find(d => d.id === req.params.id);
  if (!device) return res.redirect('/devices');
  res.render('devices/detail', { title: device.name, activePage: 'devices', device });
});

module.exports = router;
