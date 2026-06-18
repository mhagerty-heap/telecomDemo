const express = require('express');
const session = require('express-session');
const path = require('path');

const app = express();

app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, 'views'));

app.use(express.static(path.join(__dirname, 'public')));
app.use(express.urlencoded({ extended: true }));
app.use(express.json());

app.use(session({
  secret: 'nexus-mobile-secret',
  resave: false,
  saveUninitialized: false,
  cookie: { maxAge: 1000 * 60 * 60 * 2 } // 2 hours
}));

// Make session user available in all views
app.use((req, res, next) => {
  res.locals.user = req.session.user || null;
  next();
});

// Routes
app.use('/', require('./routes/home'));
app.use('/', require('./routes/auth'));
app.use('/plans', require('./routes/plans'));
app.use('/deals', require('./routes/deals'));
app.use('/coverage', require('./routes/coverage'));
app.use('/devices', require('./routes/devices'));
app.use('/checkout', require('./routes/checkout'));
app.use('/account', require('./routes/account'));
app.use('/support', require('./routes/support'));
app.use('/stores', require('./routes/stores'));

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`Nexus Mobile running at http://localhost:${PORT}`);
});
