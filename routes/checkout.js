const express = require('express');
const router = express.Router();
const plans = require('../data/plans.json');
const devices = require('../data/devices.json');

router.get('/plan', (req, res) => {
  const selectedPlanId = req.query.planId || req.session.checkout?.planId || '';
  // Carry deviceId from PDP into session so it survives the plan step
  if (req.query.deviceId) {
    req.session.checkout = { ...req.session.checkout, deviceId: req.query.deviceId };
  }
  res.render('checkout/plan', { title: 'Choose a Plan', activePage: null, plans, step: 1, selectedPlanId });
});

router.post('/plan', (req, res) => {
  // Preserve deviceId if already set (e.g. came from PDP)
  req.session.checkout = { deviceId: req.session.checkout?.deviceId || null, planId: req.body.planId };
  res.redirect('/checkout/device');
});

router.get('/device', (req, res) => {
  // Accept deviceId from query param (PDP "Add to Existing Plan") or session
  if (req.query.deviceId) {
    req.session.checkout = { ...req.session.checkout, deviceId: req.query.deviceId };
  }
  const selectedDeviceId = req.session.checkout?.deviceId || '';
  res.render('checkout/device', { title: 'Choose a Device', activePage: null, devices, step: 2, selectedDeviceId });
});

router.post('/device', (req, res) => {
  req.session.checkout = { ...req.session.checkout, deviceId: req.body.deviceId || null };
  res.redirect('/checkout/details');
});

router.get('/details', (req, res) => {
  res.render('checkout/details', { title: 'Your Information', activePage: null, step: 3, errors: {}, formData: {} });
});

router.post('/details', (req, res) => {
  const { firstName, lastName, email, phone, address, city, state, zip } = req.body;
  const errors = {};
  if (!firstName) errors.firstName = 'First name is required';
  if (!lastName) errors.lastName = 'Last name is required';
  if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) errors.email = 'Valid email is required';
  if (!phone) errors.phone = 'Phone number is required';
  if (!address) errors.address = 'Address is required';
  if (!city) errors.city = 'City is required';
  if (!state) errors.state = 'State is required';
  if (!zip || !/^\d{5}$/.test(zip)) errors.zip = 'Valid 5-digit ZIP is required';

  if (Object.keys(errors).length > 0) {
    return res.render('checkout/details', {
      title: 'Your Information', activePage: null, step: 3,
      errors, formData: req.body
    });
  }

  req.session.checkout = { ...req.session.checkout, customer: req.body };
  res.redirect('/checkout/confirm');
});

router.get('/confirm', (req, res) => {
  const cart = req.session.checkout || {};
  const plan = plans.find(p => p.id === cart.planId) || null;
  const device = cart.deviceId ? devices.find(d => d.id === cart.deviceId) : null;
  res.render('checkout/confirm', { title: 'Review & Confirm', activePage: null, step: 4, plan, device, customer: cart.customer });
});

router.post('/confirm', (req, res) => {
  req.session.checkout = {};
  res.redirect('/checkout/success');
});

router.get('/success', (req, res) => {
  res.render('checkout/success', { title: 'Order Confirmed', activePage: null });
});

module.exports = router;
