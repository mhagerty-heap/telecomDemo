const express = require('express');
const router = express.Router();
const user = require('../data/user.json');

router.get('/login', (req, res) => {
  if (req.session.user) return res.redirect('/account');
  res.render('login', {
    title: 'Log In',
    activePage: 'login',
    error: null,
    email: ''
  });
});

// Demo login: any well-formed email signs in (the email is the analytics
// identity); the password is ignored. Profile data comes from user.json.
router.post('/login', (req, res) => {
  const email = (req.body.email || '').trim();
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
    return res.render('login', {
      title: 'Log In',
      activePage: 'login',
      error: 'Please enter a valid email address.',
      email
    });
  }
  req.session.user = { name: user.name, email, accountId: user.accountId };
  const returnTo = req.session.returnTo || '/account';
  delete req.session.returnTo;
  res.redirect(returnTo);
});

router.get('/logout', (req, res) => {
  req.session.destroy(() => {
    res.redirect('/');
  });
});

module.exports = router;
