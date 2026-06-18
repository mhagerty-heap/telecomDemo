const express = require('express');
const router = express.Router();
const { requireAuth } = require('../middleware/auth');
const userData = require('../data/user.json');
const plans = require('../data/plans.json');

router.use(requireAuth);

router.get('/', (req, res) => {
  res.render('account/dashboard', { title: 'My Account', activePage: 'dashboard', account: userData });
});

router.get('/bill', (req, res) => {
  res.render('account/bill', { title: 'Bill & Payments', activePage: 'bill', account: userData, paid: req.query.paid === 'true' });
});

router.post('/bill/pay', (req, res) => {
  res.redirect('/account/bill?paid=true');
});

router.get('/plan', (req, res) => {
  res.render('account/plan', { title: 'My Plan', activePage: 'plan', account: userData, plans, upgraded: req.query.upgraded === 'true' });
});

router.post('/plan/upgrade', (req, res) => {
  res.redirect('/account/plan?upgraded=true');
});

router.get('/lines', (req, res) => {
  res.render('account/lines', { title: 'Manage Lines', activePage: 'lines', account: userData });
});

router.get('/devices', (req, res) => {
  res.render('account/devices', { title: 'My Devices', activePage: 'devices', account: userData });
});

router.get('/profile', (req, res) => {
  res.render('account/profile', { title: 'Profile & Settings', activePage: 'profile', account: userData, saved: req.query.saved === 'true' });
});

router.post('/profile', (req, res) => {
  res.redirect('/account/profile?saved=true');
});

module.exports = router;
