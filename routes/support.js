const express = require('express');
const router = express.Router();

router.get('/', (req, res) => {
  res.render('support/index', { title: 'Support', activePage: 'support' });
});

router.get('/troubleshoot', (req, res) => {
  res.render('support/troubleshoot', { title: 'Troubleshooter', activePage: 'support', step: 1 });
});

router.get('/outages', (req, res) => {
  const { zip } = req.query;
  let status = null;
  if (zip) {
    // Simulate: zip starting with '9' has a minor outage, others are clear
    status = zip.startsWith('9')
      ? { type: 'warning', message: 'Minor service disruption reported in your area. Our team is working on it.' }
      : { type: 'ok', message: 'No outages detected in your area. All systems normal.' };
  }
  res.render('support/outages', { title: 'Outage Checker', activePage: 'support', zip: zip || '', status });
});

router.get('/contact', (req, res) => {
  res.render('support/contact', { title: 'Contact Us', activePage: 'support', submitted: false, errors: {}, formData: {} });
});

router.post('/contact', (req, res) => {
  const { name, email, topic, message } = req.body;
  const errors = {};
  if (!name) errors.name = 'Name is required';
  if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) errors.email = 'Valid email is required';
  if (!topic) errors.topic = 'Please select a topic';
  if (!message || message.length < 10) errors.message = 'Please provide more detail (at least 10 characters)';

  if (Object.keys(errors).length > 0) {
    return res.render('support/contact', {
      title: 'Contact Us', activePage: 'support',
      submitted: false, errors, formData: req.body
    });
  }
  res.render('support/contact', {
    title: 'Contact Us', activePage: 'support',
    submitted: true, errors: {}, formData: {}
  });
});

module.exports = router;
