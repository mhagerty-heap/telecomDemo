const express = require('express');
const router = express.Router();
const user = require('../data/user.json');

const DEMO_EMAIL = 'demo@nexusmobile.com';
const DEMO_PASSWORD = 'demo123';

router.get('/login', (req, res) => {
  if (req.session.user) return res.redirect('/account');
  res.render('login', {
    title: 'Log In',
    activePage: 'login',
    error: null,
    email: ''
  });
});

router.post('/login', (req, res) => {
  const { email, password } = req.body;
  if (email === DEMO_EMAIL && password === DEMO_PASSWORD) {
    req.session.user = { name: user.name, email: user.email, accountId: user.accountId };
    const returnTo = req.session.returnTo || '/account';
    delete req.session.returnTo;
    return res.redirect(returnTo);
  }
  res.render('login', {
    title: 'Log In',
    activePage: 'login',
    error: 'Incorrect email or password. Please try again.',
    email
  });
});

router.get('/logout', (req, res) => {
  req.session.destroy(() => {
    res.redirect('/');
  });
});

module.exports = router;
