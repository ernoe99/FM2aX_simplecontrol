import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import math
from datetime import datetime, timedelta
import numpy as np
from scipy.stats import norm
from scipy.optimize import brentq
import json
import os
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class OptionsManager:
    def __init__(self, root):
        self.root = root
        self.root.title("Options Trading Manager")
        self.root.geometry("1200x800")

        # Data storage
        self.positions = []
        self.closed_positions = []
        self.total_winloss = 0.0

        self.setup_gui()

    def setup_gui(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Save Portfolio", command=self.save_portfolio)
        file_menu.add_command(label="Load Portfolio", command=self.load_portfolio)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

        # Create notebook for tabs
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)

        # Input tab
        self.input_frame = ttk.Frame(notebook)
        notebook.add(self.input_frame, text="Add Position")
        self.setup_input_tab()

        # Positions tab
        self.positions_frame = ttk.Frame(notebook)
        notebook.add(self.positions_frame, text="Open Positions")
        self.setup_positions_tab()

        # Closed positions tab
        self.closed_frame = ttk.Frame(notebook)
        notebook.add(self.closed_frame, text="Closed Positions")
        self.setup_closed_tab()

        # Win/Loss summary
        self.summary_frame = ttk.Frame(self.root)
        self.summary_frame.pack(fill='x', padx=10, pady=5)
        self.winloss_label = ttk.Label(self.summary_frame, text=f"Total Win/Loss: ${self.total_winloss:.2f}",
                                       font=('Arial', 12, 'bold'))
        self.winloss_label.pack()

    def setup_input_tab(self):
        # Input fields
        fields_frame = ttk.LabelFrame(self.input_frame, text="Position Details", padding=10)
        fields_frame.pack(fill='x', padx=10, pady=10)

        # Ticker symbol
        ttk.Label(fields_frame, text="Ticker Symbol:").grid(row=0, column=0, sticky='w', pady=2)
        self.ticker_var = tk.StringVar()
        self.ticker_entry = ttk.Entry(fields_frame, textvariable=self.ticker_var)
        self.ticker_entry.grid(row=0, column=1, sticky='ew', pady=2)

        # Option type
        ttk.Label(fields_frame, text="Position Type:").grid(row=1, column=0, sticky='w', pady=2)
        self.option_type = ttk.Combobox(fields_frame, values=['Call', 'Put', 'Stock'], state='readonly')
        self.option_type.grid(row=1, column=1, sticky='ew', pady=2)
        self.option_type.set('Call')
        self.option_type.bind('<<ComboboxSelected>>', self.on_position_type_change)

        # Position type
        ttk.Label(fields_frame, text="Trade Type:").grid(row=2, column=0, sticky='w', pady=2)
        self.position_type = ttk.Combobox(fields_frame, values=['Buy (Long)', 'Sell (Short)'], state='readonly',
                                          width=12)
        self.position_type.grid(row=2, column=1, sticky='ew', pady=2)
        self.position_type.set('Buy (Long)')

        # Strike price
        ttk.Label(fields_frame, text="Strike Price:").grid(row=3, column=0, sticky='w', pady=2)
        self.strike_var = tk.DoubleVar()
        self.strike_entry = ttk.Entry(fields_frame, textvariable=self.strike_var)
        self.strike_entry.grid(row=3, column=1, sticky='ew', pady=2)
        self.strike_entry.bind('<KeyRelease>', self.calculate_iv)

        # Current underlying price
        ttk.Label(fields_frame, text="Current Underlying Price:").grid(row=4, column=0, sticky='w', pady=2)
        self.underlying_var = tk.DoubleVar()
        self.underlying_entry = ttk.Entry(fields_frame, textvariable=self.underlying_var)
        self.underlying_entry.grid(row=4, column=1, sticky='ew', pady=2)
        self.underlying_entry.bind('<KeyRelease>', self.calculate_iv)

        # Open price
        ttk.Label(fields_frame, text="Open Price (per contract):").grid(row=5, column=0, sticky='w', pady=2)
        self.open_price_var = tk.DoubleVar()
        self.open_price_entry = ttk.Entry(fields_frame, textvariable=self.open_price_var)
        self.open_price_entry.grid(row=5, column=1, sticky='ew', pady=2)
        self.open_price_entry.bind('<KeyRelease>', self.calculate_iv)

        # Number of contracts
        ttk.Label(fields_frame, text="Number of Contracts:").grid(row=6, column=0, sticky='w', pady=2)
        self.contracts_var = tk.IntVar(value=1)
        self.contracts_entry = ttk.Entry(fields_frame, textvariable=self.contracts_var)
        self.contracts_entry.grid(row=6, column=1, sticky='ew', pady=2)

        # Helper label for contracts
        helper_label = ttk.Label(fields_frame, text="(Negative = Short position)", font=('Arial', 8), foreground='gray')
        helper_label.grid(row=6, column=2, columnspan=2, sticky='w', pady=2, padx=(10, 0))

        # Contract size
        self.contract_size_label = ttk.Label(fields_frame, text="Contract Size:")
        self.contract_size_label.grid(row=7, column=0, sticky='w', pady=2)
        self.contract_size_var = tk.IntVar(value=100)
        self.contract_size_entry = ttk.Entry(fields_frame, textvariable=self.contract_size_var)
        self.contract_size_entry.grid(row=7, column=1, sticky='ew', pady=2)

        # Helper label for contract size
        self.contract_size_helper = ttk.Label(fields_frame, text="(100 for options, 1 for stocks)", font=('Arial', 8),
                                              foreground='gray')
        self.contract_size_helper.grid(row=7, column=2, columnspan=2, sticky='w', pady=2, padx=(10, 0))

        # Expiration date
        ttk.Label(fields_frame, text="Expiration Date (YYYY-MM-DD):").grid(row=8, column=0, sticky='w', pady=2)
        self.expiry_var = tk.StringVar()
        self.expiry_entry = ttk.Entry(fields_frame, textvariable=self.expiry_var)
        self.expiry_entry.grid(row=8, column=1, sticky='ew', pady=2)
        self.expiry_entry.bind('<KeyRelease>', self.calculate_iv)

        # Risk-free rate
        ttk.Label(fields_frame, text="Risk-free Rate (%):").grid(row=9, column=0, sticky='w', pady=2)
        self.rate_var = tk.DoubleVar(value=5.0)
        self.rate_entry = ttk.Entry(fields_frame, textvariable=self.rate_var)
        self.rate_entry.grid(row=9, column=1, sticky='ew', pady=2)
        self.rate_entry.bind('<KeyRelease>', self.calculate_iv)

        # Dividend yield
        ttk.Label(fields_frame, text="Dividend Yield (%):").grid(row=10, column=0, sticky='w', pady=2)
        self.dividend_var = tk.DoubleVar(value=0.0)
        self.dividend_entry = ttk.Entry(fields_frame, textvariable=self.dividend_var)
        self.dividend_entry.grid(row=10, column=1, sticky='ew', pady=2)
        self.dividend_entry.bind('<KeyRelease>', self.calculate_iv)

        # Configure grid weights
        fields_frame.columnconfigure(1, weight=1)
        fields_frame.columnconfigure(3, weight=1)

        # Calculated values frame
        calc_frame = ttk.LabelFrame(self.input_frame, text="Calculated Values", padding=10)
        calc_frame.pack(fill='x', padx=10, pady=10)

        # Days to maturity
        ttk.Label(calc_frame, text="Days to Maturity:").grid(row=0, column=0, sticky='w', pady=2)
        self.days_label = ttk.Label(calc_frame, text="N/A")
        self.days_label.grid(row=0, column=1, sticky='w', pady=2)

        # Years to maturity
        ttk.Label(calc_frame, text="Years to Maturity:").grid(row=1, column=0, sticky='w', pady=2)
        self.years_label = ttk.Label(calc_frame, text="N/A")
        self.years_label.grid(row=1, column=1, sticky='w', pady=2)

        # Implied volatility
        ttk.Label(calc_frame, text="Implied Volatility (%):").grid(row=2, column=0, sticky='w', pady=2)
        self.iv_label = ttk.Label(calc_frame, text="N/A")
        self.iv_label.grid(row=2, column=1, sticky='w', pady=2)

        # Total premium
        ttk.Label(calc_frame, text="Total Premium:").grid(row=3, column=0, sticky='w', pady=2)
        self.premium_label = ttk.Label(calc_frame, text="N/A")
        self.premium_label.grid(row=3, column=1, sticky='w', pady=2)

        # Add position button
        ttk.Button(self.input_frame, text="Add Position", command=self.add_position).pack(pady=10)

    def setup_positions_tab(self):
        # Main container with left and right sections
        main_container = ttk.Frame(self.positions_frame)
        main_container.pack(fill='both', expand=True, padx=10, pady=10)

        # Left section for treeview
        left_frame = ttk.Frame(main_container)
        left_frame.pack(side='left', fill='both', expand=True)

        # Treeview for positions
        columns = (
        'Ticker', 'Trade', 'Type', 'Strike', 'Contracts', 'Open Price', 'Days Left', 'IV%', 'Premium', 'Risk Up',
        'Risk Down')
        self.positions_tree = ttk.Treeview(left_frame, columns=columns, show='headings', height=15)

        for col in columns:
            self.positions_tree.heading(col, text=col)
            if col in ['Ticker', 'Trade']:
                self.positions_tree.column(col, width=80)
            else:
                self.positions_tree.column(col, width=100)

        # Scrollbar
        scrollbar = ttk.Scrollbar(left_frame, orient='vertical', command=self.positions_tree.yview)
        self.positions_tree.configure(yscrollcommand=scrollbar.set)

        self.positions_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        right_frame = ttk.Frame(main_container, width=250)
        right_frame.pack(side='right', fill='y', padx=(10, 0))
        right_frame.pack_propagate(False)

        # Current underlying price input
        price_frame = ttk.LabelFrame(right_frame, text="Market Data", padding=10)
        price_frame.pack(fill='x', pady=(0, 10))

        ttk.Label(price_frame, text="Current Underlying Price:").pack(anchor='w')
        self.current_underlying_var = tk.DoubleVar(value=100.0)
        self.current_underlying_entry = ttk.Entry(price_frame, textvariable=self.current_underlying_var)
        self.current_underlying_entry.pack(fill='x', pady=(2, 0))

        # Risk summary - vertical layout
        risk_summary_frame = ttk.LabelFrame(right_frame, text="Risk Summary", padding=10)
        risk_summary_frame.pack(fill='x', pady=(0, 10))

        self.total_premium_label = ttk.Label(risk_summary_frame, text="Total Premium: $0.00",
                                             font=('Arial', 10, 'bold'))
        self.total_premium_label.pack(anchor='w', pady=2)

        self.total_uprisk_label = ttk.Label(risk_summary_frame, text="Total Up Risk: $0.00", font=('Arial', 10, 'bold'))
        self.total_uprisk_label.pack(anchor='w', pady=2)

        self.total_downrisk_label = ttk.Label(risk_summary_frame, text="Total Down Risk: $0.00",
                                              font=('Arial', 10, 'bold'))
        self.total_downrisk_label.pack(anchor='w', pady=2)

        self.total_risk_label = ttk.Label(risk_summary_frame, text="Combined Risk: $0.00", font=('Arial', 10, 'bold'))
        self.total_risk_label.pack(anchor='w', pady=2)

        # Buttons frame - vertical layout
        buttons_frame = ttk.LabelFrame(right_frame, text="Actions", padding=10)
        buttons_frame.pack(fill='x')

        ttk.Button(buttons_frame, text="Close Position", command=self.close_position).pack(fill='x', pady=2)
        ttk.Button(buttons_frame, text="Delete Position", command=self.delete_position).pack(fill='x', pady=2)
        ttk.Button(buttons_frame, text="Show Portfolio Graph", command=self.show_portfolio_graph).pack(fill='x', pady=2)
        ttk.Button(buttons_frame, text="Refresh", command=self.refresh_positions).pack(fill='x', pady=2)
        ttk.Button(buttons_frame, text="Save Portfolio", command=self.save_portfolio).pack(fill='x', pady=2)
        ttk.Button(buttons_frame, text="Load Portfolio", command=self.load_portfolio).pack(fill='x', pady=2)

    def setup_closed_tab(self):
        # Main container for closed positions
        main_container = ttk.Frame(self.closed_frame)
        main_container.pack(fill='both', expand=True, padx=10, pady=10)

        # Treeview for closed positions
        columns = ('Ticker', 'Type', 'Strike', 'Contracts', 'Open Price', 'Close Price', 'Win/Loss')
        self.closed_tree = ttk.Treeview(main_container, columns=columns, show='headings', height=15)

        for col in columns:
            self.closed_tree.heading(col, text=col)
            self.closed_tree.column(col, width=120)

        # Scrollbar
        closed_scrollbar = ttk.Scrollbar(main_container, orient='vertical', command=self.closed_tree.yview)
        self.closed_tree.configure(yscrollcommand=closed_scrollbar.set)

        self.closed_tree.pack(side='left', fill='both', expand=True)
        closed_scrollbar.pack(side='right', fill='y')

        summary_frame = ttk.LabelFrame(self.closed_frame, text="Closed Positions Summary", padding=10)
        summary_frame.pack(fill='x', padx=10, pady=(0, 10))

        self.closed_winloss_label = ttk.Label(summary_frame, text="Total Closed Win/Loss: $0.00",
                                              font=('Arial', 12, 'bold'))
        self.closed_winloss_label.pack()

    def black_scholes(self, S, K, T, r, q, sigma, option_type):
        """Calculate Black-Scholes option price"""
        if T <= 0:
            if option_type == 'Call':
                return max(S - K, 0)
            else:
                return max(K - S, 0)

        if S <= 0 or K <= 0 or sigma <= 0:
            return 0

        try:
            d1 = (math.log(S / K) + (r - q + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
            d2 = d1 - sigma * math.sqrt(T)

            if option_type == 'Call':
                price = S * math.exp(-q * T) * norm.cdf(d1) - K * math.exp(-r * T) * norm.cdf(d2)
            else:
                price = K * math.exp(-r * T) * norm.cdf(-d2) - S * math.exp(-q * T) * norm.cdf(-d1)

            return max(price, 0)  # Ensure non-negative price
        except (ValueError, ZeroDivisionError):
            return 0

    def calculate_implied_volatility(self, market_price, S, K, T, r, q, option_type):
        """Calculate implied volatility using Brent's method"""
        if T <= 0 or S <= 0 or K <= 0 or market_price <= 0:
            return 0

        def objective(sigma):
            try:
                return self.black_scholes(S, K, T, r, q, sigma, option_type) - market_price
            except:
                return float('inf')

        try:
            intrinsic_value = max(S - K, 0) if option_type == 'Call' else max(K - S, 0)
            if market_price < intrinsic_value * 0.01:  # Too low
                return 0

            iv = brentq(objective, 0.001, 5.0, xtol=1e-6)
            return iv * 100  # Convert to percentage
        except (ValueError, RuntimeError):
            return 0

    def calculate_time_to_expiry(self, expiry_str):
        """Calculate days and years to expiry"""
        try:
            expiry_date = datetime.strptime(expiry_str, '%Y-%m-%d')
            today = datetime.now()
            days = (expiry_date - today).days
            years = days / 365.25
            return days, years
        except:
            return 0, 0

    def calculate_iv(self, event=None):
        """Calculate and display implied volatility and other metrics"""
        try:
            strike = self.strike_var.get() if self.strike_var.get() > 0 else 0
            underlying = self.underlying_var.get() if self.underlying_var.get() > 0 else 0
            open_price = self.open_price_var.get() if self.open_price_var.get() > 0 else 0
            expiry = self.expiry_var.get().strip()
            rate = self.rate_var.get() / 100
            dividend = self.dividend_var.get() / 100
            option_type = self.option_type.get()
            contracts = self.contracts_var.get() if self.contracts_var.get() > 0 else 0
            contract_size = self.contract_size_var.get() if self.contract_size_var.get() > 0 else 100

            if option_type == 'Stock':
                # For stocks, we don't need expiry or IV calculations
                self.days_label.config(text="N/A")
                self.years_label.config(text="N/A")
                self.iv_label.config(text="N/A")

                self.premium_label.config(text="$0.00")
            else:
                # Original option calculations
                if all([strike > 0, underlying > 0, open_price > 0, expiry]):
                    days, years = self.calculate_time_to_expiry(expiry)
                    self.days_label.config(text=f"{days}")
                    self.years_label.config(text=f"{years:.4f}")

                    if years > 0:
                        iv = self.calculate_implied_volatility(open_price, underlying, strike, years, rate, dividend,
                                                               option_type)
                        self.iv_label.config(text=f"{iv:.2f}%")

                        temp_position = {
                            'option_type': option_type,
                            'open_price': open_price,
                            'underlying_price': underlying,
                            'strike': strike,
                            'contracts': abs(contracts),
                            'contract_size': contract_size
                        }
                        total_premium = self.calculate_premium(temp_position)
                        self.premium_label.config(text=f"${total_premium:.2f}")
                    else:
                        self.iv_label.config(text="Expired")
                        self.premium_label.config(text="$0.00")
                else:
                    self.days_label.config(text="N/A")
                    self.years_label.config(text="N/A")
                    self.iv_label.config(text="N/A")
                    self.premium_label.config(text="N/A")
        except Exception as e:
            # Reset labels on any error
            self.days_label.config(text="N/A")
            self.years_label.config(text="N/A")
            self.iv_label.config(text="N/A")
            self.premium_label.config(text="N/A")

    def calculate_intrinsic_value(self, S, K, option_type):
        """Calculate intrinsic value of option or stock value"""
        if option_type == 'Stock':
            return S  # For stocks, "intrinsic value" is just the current price
        elif option_type == 'Call':
            return max(0, S - K)
        else:  # Put
            return max(0, K - S)

    def calculate_risk(self, position):
        """Calculate risk for up and down movements using original version logic"""
        S = position['underlying_price']
        K = position['strike']
        option_type = position['option_type']
        contracts = position['contracts']
        contract_size = position['contract_size']

        # Calculate intrinsic values at different price levels
        S_up = S * 1.5
        S_down = S * 0.5

        current_intrinsic = self.calculate_intrinsic_value(S, K, option_type)
        intrinsic_up = self.calculate_intrinsic_value(S_up, K, option_type)
        intrinsic_down = self.calculate_intrinsic_value(S_down, K, option_type)

        is_long = contracts > 0

        if option_type == 'Stock':
            if is_long:  # Long stock
                risk_up = -(intrinsic_up - current_intrinsic) * abs(contracts) * contract_size  # Unlimited upside potential
                risk_down = -(intrinsic_down - current_intrinsic) * abs(contracts) * contract_size
            else:  # Short stock
                risk_up = (intrinsic_up - current_intrinsic) * abs(contracts) * contract_size
                risk_down = (intrinsic_down - current_intrinsic) * abs(contracts) * contract_size  # Unlimited downside potential (for short seller)
        elif option_type == 'Call':
            if is_long:  # Long call
                risk_up = -(intrinsic_up - current_intrinsic) * abs(contracts) * contract_size
                risk_down = 0
            else:  # Short call
                risk_up = (intrinsic_up - current_intrinsic) * abs(contracts) * contract_size
                risk_down = 0
        else:  # Put
            if is_long:  # Long put
                risk_up = 0
                risk_down = -(intrinsic_down - current_intrinsic) * abs(contracts) * contract_size
            else:  # Short put
                risk_up = 0
                risk_down = (intrinsic_down - current_intrinsic) * abs(contracts) * contract_size

        return risk_up, risk_down

    def calculate_premium(self, position):
        """Calculate premium - positive for long positions, negative for short positions"""
        option_type = position['option_type']
        open_price = position['open_price']
        underlying_price = position['underlying_price']
        strike = position['strike']
        contracts = position['contracts']
        contract_size = position['contract_size']

        if option_type == 'Stock':
            return 0.0
        else:
            if option_type == 'Call':
                intrinsic_value = max(underlying_price - strike, 0)
            else:  # Put
                intrinsic_value = max(strike - underlying_price, 0)

            # For long positions (positive contracts)

            premium = (open_price - intrinsic_value) * contracts * contract_size
            print("Prämium = ", premium)

            return premium

    def add_position(self):
        """Add a new position"""
        try:
            ticker = self.ticker_var.get().strip().upper()
            if not ticker:
                messagebox.showerror("Error", "Please enter a ticker symbol")
                return

            underlying = self.underlying_var.get()
            contracts = self.contracts_var.get()
            contract_size = self.contract_size_var.get()
            position_type = self.position_type.get()
            option_type = self.option_type.get()

            if option_type == 'Stock':
                # For stocks, we only need underlying price, contracts, and contract size
                if not all([underlying > 0, contracts != 0, contract_size > 0]):
                    messagebox.showerror("Error", "Please fill in underlying price, contracts, and contract size")
                    return

                strike = underlying  # For stocks, use current price as "strike" for consistency
                open_price = underlying  # For stocks, open price is current price
                expiry = "2099-12-31"  # Far future date for stocks (no expiry)
                days, years = 36500, 100  # Large values for stocks
                iv = 0  # No IV for stocks
            else:
                # Original option validation
                strike = self.strike_var.get()
                open_price = self.open_price_var.get()
                expiry = self.expiry_var.get().strip()

                if not all([strike > 0, underlying > 0, open_price > 0, expiry]):
                    messagebox.showerror("Error",
                                         "Please fill in all fields with valid values (contracts can be negative for short positions)")
                    return

                days, years = self.calculate_time_to_expiry(expiry)

                if years <= 0:
                    messagebox.showerror("Error", "Expiration date must be in the future")
                    return

                iv = self.calculate_implied_volatility(
                    open_price,
                    underlying,
                    strike,
                    years,
                    self.rate_var.get() / 100,
                    self.dividend_var.get() / 100,
                    option_type
                )

            if position_type == 'Sell (Short)' and contracts > 0:
                contracts = -contracts
            elif position_type == 'Buy (Long)' and contracts < 0:
                contracts = abs(contracts)

            temp_position = {
                'option_type': option_type,
                'open_price': open_price,
                'underlying_price': underlying,
                'strike': strike,
                'contracts': contracts,
                'contract_size': contract_size
            }
            total_premium = self.calculate_premium(temp_position)

            position = {
                'ticker': ticker,
                'option_type': option_type,
                'position_type': position_type,
                'strike': strike,
                'underlying_price': underlying,
                'open_price': open_price,
                'contracts': contracts,
                'contract_size': contract_size,
                'expiry_date': expiry,
                'days_to_expiry': days,
                'years_to_expiry': years,
                'rate': self.rate_var.get() / 100,
                'dividend': self.dividend_var.get() / 100,
                'iv': iv,
                'premium': total_premium
            }

            self.positions.append(position)
            self.refresh_positions()
            messagebox.showinfo("Success", "Position added successfully!")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to add position: {str(e)}")

    def clear_inputs(self):
        """Clear all input fields"""
        self.strike_var.set(0)
        self.underlying_var.set(0)
        self.open_price_var.set(0)
        self.contracts_var.set(1)
        self.expiry_var.set("")
        self.days_label.config(text="N/A")
        self.years_label.config(text="N/A")
        self.iv_label.config(text="N/A")
        self.premium_label.config(text="N/A")

    def refresh_positions(self):
        """Refresh the positions display"""
        # Clear existing items
        for item in self.positions_tree.get_children():
            self.positions_tree.delete(item)

        total_uprisk = 0
        total_downrisk = 0
        total_premium = 0

        # Add current positions
        for i, pos in enumerate(self.positions):
            days, years = self.calculate_time_to_expiry(pos['expiry_date'])
            pos['days_to_expiry'] = days
            pos['years_to_expiry'] = years

            risk_up, risk_down = self.calculate_risk(pos)

            total_uprisk += risk_up
            total_downrisk += risk_down
            total_premium += pos['premium']

            position_display = pos.get('position_type', 'Buy (Long)' if pos['contracts'] > 0 else 'Sell (Short)')

            self.positions_tree.insert('', 'end', values=(
                pos.get('ticker', 'N/A'),
                position_display,
                pos['option_type'],
                f"${pos['strike']:.2f}",
                pos['contracts'],
                f"${pos['open_price']:.2f}",
                days,
                f"{pos['iv']:.2f}%",
                f"${pos['premium']:.2f}",
                f"${risk_up:.2f}",
                f"${risk_down:.2f}"
            ))

        self.total_premium_label.config(text=f"Total Premium: ${total_premium:.2f}")
        self.total_uprisk_label.config(text=f"Total Up Risk: ${total_uprisk:.2f}")
        self.total_downrisk_label.config(text=f"Total Down Risk: ${total_downrisk:.2f}")

        combined_risk = max(total_uprisk,total_downrisk)
        self.total_risk_label.config(text=f"Combined Risk: ${combined_risk:.2f}")

    def close_position(self):
        """Close a selected position"""
        selection = self.positions_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a position to close")
            return

        item = selection[0]
        index = self.positions_tree.index(item)
        position = self.positions[index]

        close_price = tk.simpledialog.askfloat("Close Position",
                                               f"Enter close price for {position.get('ticker', 'N/A')} {position['option_type']} ${position['strike']:.2f}:")

        if close_price is None:
            return

        contracts = position['contracts']
        contract_size = position['contract_size']
        open_value = position['open_price'] * abs(contracts) * contract_size
        close_value = close_price * abs(contracts) * contract_size

        if contracts > 0:  # Long position
            winloss = close_value - open_value
        else:  # Short position
            winloss = open_value - close_value

        closed_position = {
            'ticker': position.get('ticker', 'N/A'),
            'option_type': position['option_type'],
            'position_type': position.get('position_type', 'Buy (Long)' if contracts > 0 else 'Sell (Short)'),
            'strike': position['strike'],
            'contracts': contracts,
            'open_price': position['open_price'],
            'close_price': close_price,
            'winloss': winloss
        }

        self.total_winloss += winloss
        self.winloss_label.config(text=f"Total Win/Loss: ${self.total_winloss:.2f}")

        self.closed_positions.append(closed_position)
        self.positions.pop(index)

        self.refresh_positions()
        self.refresh_closed_positions()

        messagebox.showinfo("Success", f"Position closed. Win/Loss: ${winloss:.2f}")

    def refresh_closed_positions(self):
        """Refresh the closed positions display"""
        # Clear existing items
        for item in self.closed_tree.get_children():
            self.closed_tree.delete(item)

        total_closed_winloss = 0

        # Add closed positions
        for pos in self.closed_positions:
            position_display = pos.get('position_type', 'Buy (Long)' if pos['contracts'] > 0 else 'Sell (Short)')

            self.closed_tree.insert('', 'end', values=(
                pos.get('ticker', 'N/A'),
                f"{position_display} {pos['option_type']}",
                f"${pos['strike']:.2f}",
                pos['contracts'],
                f"${pos['open_price']:.2f}",
                f"${pos['close_price']:.2f}",
                f"${pos['winloss']:.2f}"
            ))

            total_closed_winloss += pos['winloss']

        self.closed_winloss_label.config(text=f"Total Closed Win/Loss: ${total_closed_winloss:.2f}")

    def save_portfolio(self):
        """Save current portfolio to JSON file"""
        try:
            ticker_for_filename = ""
            if self.positions:
                # Get the most common ticker from open positions
                tickers = [pos.get('ticker', '') for pos in self.positions if pos.get('ticker')]
                if tickers:
                    ticker_for_filename = f"_{max(set(tickers), key=tickers.count)}"

            default_filename = f"portfolio{ticker_for_filename}.json"

            filename = filedialog.asksaveasfilename(
                title="Save Portfolio",
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                initialfile=default_filename
            )

            if not filename:
                return

            portfolio_data = {
                'positions': self.positions,
                'closed_positions': self.closed_positions,
                'total_winloss': self.total_winloss,
                'save_date': datetime.now().isoformat()
            }

            with open(filename, 'w') as f:
                json.dump(portfolio_data, f, indent=2, default=str)

            messagebox.showinfo("Success", f"Portfolio saved successfully to {os.path.basename(filename)}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save portfolio: {str(e)}")

    def load_portfolio(self):
        """Load portfolio from JSON file"""
        try:
            filename = filedialog.askopenfilename(
                title="Load Portfolio",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )

            if not filename:
                return

            if self.positions or self.closed_positions:
                result = messagebox.askyesno(
                    "Confirm Load",
                    "Loading a portfolio will replace your current data. Continue?"
                )
                if not result:
                    return

            with open(filename, 'r') as f:
                portfolio_data = json.load(f)

            self.positions = portfolio_data.get('positions', [])
            self.closed_positions = portfolio_data.get('closed_positions', [])
            self.total_winloss = portfolio_data.get('total_winloss', 0.0)

            self.refresh_positions()
            self.refresh_closed_positions()
            self.winloss_label.config(text=f"Total Win/Loss: ${self.total_winloss:.2f}")

            save_date = portfolio_data.get('save_date', 'Unknown')
            messagebox.showinfo("Success",
                                f"Portfolio loaded successfully from {os.path.basename(filename)}\n"
                                f"Saved on: {save_date[:19] if save_date != 'Unknown' else save_date}")

        except FileNotFoundError:
            messagebox.showerror("Error", "File not found")
        except json.JSONDecodeError:
            messagebox.showerror("Error", "Invalid JSON file format")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load portfolio: {str(e)}")

    def show_portfolio_graph(self):
        """Show portfolio value graph across underlying price range with both pricing methods and maturity curve"""
        if not self.positions:
            messagebox.showwarning("Warning", "No open positions to graph")
            return

        try:
            current_price = self.current_underlying_var.get()
            if current_price <= 0:
                messagebox.showerror("Error", "Please enter a valid current underlying price")
                return

            shortest_maturity = float('inf')
            for pos in self.positions:
                if pos['option_type'] != 'Stock' and pos['years_to_expiry'] < shortest_maturity:
                    shortest_maturity = pos['years_to_expiry']

            # Create price range from 0.5 to 1.5 of current price
            price_range = np.linspace(current_price * 0.5, current_price * 1.5, 100)
            portfolio_values_intrinsic = []
            portfolio_values_bs = []
            portfolio_values_maturity = []
            portfolio_values_two_weeks = []

            for price in price_range:
                total_value_intrinsic = 0
                total_value_bs = 0
                total_value_maturity = 0
                total_value_two_weeks = 0

                for pos in self.positions:
                    intrinsic_value = self.calculate_intrinsic_value(price, pos['strike'], pos['option_type'])
                    position_value_intrinsic = intrinsic_value * pos['contracts'] * pos['contract_size']
                    total_value_intrinsic += position_value_intrinsic

                    if pos['option_type'] == 'Stock':
                        # For stocks, all values are the same
                        total_value_bs += position_value_intrinsic
                        total_value_maturity += position_value_intrinsic
                        total_value_two_weeks += position_value_intrinsic
                    elif pos['years_to_expiry'] > 0:
                        bs_value = self.black_scholes(
                            price,
                            pos['strike'],
                            pos['years_to_expiry'],
                            pos['rate'],
                            pos['dividend'],
                            pos['iv'] / 100,
                            pos['option_type']
                        )
                        position_value_bs = bs_value * pos['contracts'] * pos['contract_size']
                        total_value_bs += position_value_bs

                        # At maturity, use very small time value (1 day = 1/365.25 years) for Black-Scholes
                        maturity_time = 1 / 365.25  # 1 day to expiry
                        bs_value_maturity = self.black_scholes(
                            price,
                            pos['strike'],
                            maturity_time,
                            pos['rate'],
                            pos['dividend'],
                            pos['iv'] / 100,
                            pos['option_type']
                        )
                        position_value_maturity = bs_value_maturity * pos['contracts'] * pos['contract_size']
                        total_value_maturity += position_value_maturity

                        two_weeks_time = max(0, pos['years_to_expiry'] - (14 / 365.25))  # Subtract 2 weeks
                        if two_weeks_time > 0:
                            bs_value_two_weeks = self.black_scholes(
                                price,
                                pos['strike'],
                                two_weeks_time,
                                pos['rate'],
                                pos['dividend'],
                                pos['iv'] / 100,
                                pos['option_type']
                            )
                        else:
                            # If less than 2 weeks to expiry, use intrinsic value
                            bs_value_two_weeks = intrinsic_value

                        position_value_two_weeks = bs_value_two_weeks * pos['contracts'] * pos['contract_size']
                        total_value_two_weeks += position_value_two_weeks
                    else:
                        # If expired, use intrinsic value for all
                        total_value_bs += position_value_intrinsic
                        total_value_maturity += position_value_intrinsic
                        total_value_two_weeks += position_value_intrinsic

                portfolio_values_intrinsic.append(total_value_intrinsic)
                portfolio_values_bs.append(total_value_bs)
                portfolio_values_maturity.append(total_value_maturity)
                portfolio_values_two_weeks.append(total_value_two_weeks)

            # Create new window for graph
            graph_window = tk.Toplevel(self.root)
            graph_window.title("Portfolio Value Graph - All Methods Including Two Weeks Ahead")
            graph_window.geometry("900x700")

            # Create matplotlib figure
            fig, ax = plt.subplots(figsize=(12, 8))

            ax.plot(price_range, portfolio_values_intrinsic, 'b-', linewidth=2, label='Current Intrinsic Value')
            ax.plot(price_range, portfolio_values_bs, 'r-', linewidth=2, label='Black-Scholes Theoretical')
            ax.plot(price_range, portfolio_values_two_weeks, 'm-', linewidth=2, label='Black-Scholes Two Weeks Ahead')
            if shortest_maturity != float('inf'):
                ax.plot(price_range, portfolio_values_maturity, 'g-', linewidth=2,
                        label=f'Black-Scholes at Maturity ({shortest_maturity:.2f} years)')

            ax.axhline(y=0, color='gray', linestyle='--', alpha=0.7, label='Break-even')
            ax.axvline(x=current_price, color='orange', linestyle='--', alpha=0.7,
                       label=f'Current Price (${current_price:.2f})')

            ax.set_xlabel('Underlying Price ($)')
            ax.set_ylabel('Portfolio Value ($)')
            ax.set_title('Portfolio Value vs Underlying Price (All Methods + Two Weeks Ahead)')
            ax.grid(True, alpha=0.3)
            ax.legend()

            # Format y-axis to show currency
            ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
            ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:.0f}'))

            # Embed plot in tkinter window
            canvas = FigureCanvasTkAgg(fig, graph_window)
            canvas.draw()
            canvas.get_tk_widget().pack(fill='both', expand=True, padx=10, pady=10)

            # Add toolbar for zoom/pan
            toolbar_frame = ttk.Frame(graph_window)
            toolbar_frame.pack(fill='x', padx=10, pady=(0, 10))

            from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk
            toolbar = NavigationToolbar2Tk(canvas, toolbar_frame)
            toolbar.update()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to create portfolio graph: {str(e)}")

    def on_position_type_change(self, event=None):
        """Handle position type change to update UI accordingly"""
        position_type = self.option_type.get()

        if position_type == 'Stock':
            self.contract_size_var.set(1)  # Default to 1 share per "contract"
            self.contract_size_helper.config(text="(Number of shares)")
            # For stocks, we can hide some option-specific fields or keep them for consistency
        else:
            self.contract_size_var.set(100)
            self.contract_size_helper.config(text="(100 for options, 1 for stocks)")

        self.calculate_iv()

    def delete_position(self):
        """Delete a selected position without closing it"""
        selection = self.positions_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a position to delete")
            return

        item = selection[0]
        index = self.positions_tree.index(item)
        position = self.positions[index]

        result = messagebox.askyesno("Confirm Delete",
                                     f"Are you sure you want to delete {position.get('ticker', 'N/A')} "
                                     f"{position['option_type']} ${position['strike']:.2f} position?\n\n"
                                     f"This will permanently remove the position without affecting win/loss.")

        if result:
            self.positions.pop(index)
            self.refresh_positions()
            messagebox.showinfo("Success", "Position deleted successfully")


# Import required modules for dialog
import tkinter.simpledialog


def main():
    root = tk.Tk()
    app = OptionsManager(root)
    root.mainloop()


if __name__ == "__main__":
    main()
