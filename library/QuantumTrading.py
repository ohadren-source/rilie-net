"""
🌙 NIGHT TRADER v7.0 MAS OPTIMIZED
Quantum Density-Driven Trading Engine
MISSION: DENSITY IS DESTINY | BABY → DIAMOND EVOLUTION
PRINCIPLE: Quality > Frequency | Performance Earns Capital
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
import yfinance as yf
import pandas as pd
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class TradeSignal:
    symbol: str
    action: str
    entry_price: float
    stop_loss: float
    density: float
    confidence: float
    risk_pct: float
    timestamp: str
    components: Dict
    regime: str  # NORMAL, CHAOS, STAGNATION
    
    def to_dict(self):
        return asdict(self)

@dataclass
class ExecutedTrade:
    signal_id: str
    symbol: str
    action: str
    entry_price: float
    exit_price: Optional[float]
    quantity: int
    pnl: Optional[float]
    timestamp: str
    status: str
    density: float
    
    def to_dict(self):
        return asdict(self)

class MarketRegimeDetector:
    """Detect market chaos/stagnation for risk contraction"""
    
    def __init__(self):
        self.vix_threshold_chaos = 25.0
        self.spx_dd_threshold = 0.05
        self.sharpe_stagnation = 0.5
        self.stagnation_days = 20
        
    def detect_regime(self, market_data: Dict) -> str:
        """Classify market regime"""
        vix = market_data.get('vix', 15)
        spx_dd = market_data.get('spx_dd', 0)
        sharpe_30d = market_data.get('sharpe_30d', 1.0)
        
        if vix > self.vix_threshold_chaos or spx_dd > self.spx_dd_threshold:
            return "CHAOS"
        elif sharpe_30d < self.sharpe_stagnation:
            return "STAGNATION"
        return "NORMAL"

class SignalDensity:
    """Quantum density calculator with adaptive thresholds"""
    
    def __init__(self):
        self.components = {}
        self.density_history = []
        
    def calculate_density(self, 
                         pattern_quality: float,
                         volume_confirmation: float,
                         breadth_alignment: float,
                         momentum_strength: float,
                         conviction: float) -> float:
        """Density = 5 pure signals → 1 conviction score"""
        signals = {
            'pattern_quality': min(100, max(0, pattern_quality)),
            'volume_confirmation': min(100, max(0, volume_confirmation)),
            'breadth_alignment': min(100, max(0, breadth_alignment)),
            'momentum_strength': min(100, max(0, momentum_strength)),
            'conviction_check': min(100, max(0, conviction))
        }
        
        self.components = signals
        density = sum(signals.values()) / len(signals)
        self.density_history.append(density)
        
        # Adaptive threshold (20-day percentile)
        if len(self.density_history) > 20:
            threshold = np.percentile(self.density_history[-20:], 75)
        else:
            threshold = 65
            
        return density, threshold
    
    def get_tier(self, density: float) -> str:
        if density >= 90: return "DIAMOND"
        elif density >= 85: return "GOLD"  
        elif density >= 75: return "SILVER"
        elif density >= 65: return "BRONZE"
        return "PASS"

class BreadthCalculator:
    """Yahoo Finance breadth via SPY/VIX/QQQ"""
    
    @staticmethod
    def calculate_breadth() -> float:
        """Market breadth from major indices"""
        try:
            spy = yf.Ticker('SPY').history(period='5d')
            qqq = yf.Ticker('QQQ').history(period='5d') 
            vix = yf.Ticker('^VIX').history(period='1d')
            
            if spy.empty or vix.empty:
                return 50.0
                
            spy_vol = spy['Volume'].tail(3).mean()
            vix_close = vix['Close'].iloc[-1]
            
            # Breadth = volume confidence / fear gauge
            breadth_raw = (spy_vol / 1e9) / vix_close * 100
            breadth = min(100, max(0, breadth_raw))
            
            return breadth
        except:
            return 50.0  # Neutral on error

class PatternDetector:
    """Enhanced pattern detection"""
    
    @staticmethod
    def detect_breakout(symbol: str) -> Tuple[bool, float]:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period='1mo')
        
        if len(hist) < 20:
            return False, 0
            
        prices = hist['High'].values
        recent = prices[-5:]
        previous = prices[-20:-5]
        
        prev_high = max(previous)
        current_high = max(recent)
        
        breakout = current_high > prev_high * 1.02
        strength = (current_high - prev_high) / prev_high * 100
        return breakout, min(100, strength)

class NightTraderEngine:
    """MAS Quantum Trading Engine - Density Evolves"""
    
    def __init__(self, initial_balance: float = 100000):
        self.balance = initial_balance
        self.risk_pct = 0.10  # Starts conservative, earns more
        self.max_risk_cap = 0.30
        self.max_trades_day = 9
        
        self.signal_density = SignalDensity()
        self.regime_detector = MarketRegimeDetector()
        self.trades_today = 0
        self.trade_history = []
        self.density_history = []
        
        self.fortune_100 = [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'JPM', 
            'V', 'JNJ', 'UNH', 'HD', 'PG', 'MA', 'PFE', 'BAC', 'KO', 'XOM'
        ]
        
        logger.info(f"🌙 NIGHT TRADER v7.0 INIT | Balance: ${self.balance:,.0f} | Risk: {self.risk_pct*100}%")
    
    def get_market_regime(self) -> Dict:
        """Fetch current market conditions"""
        vix_data = yf.Ticker('^VIX').history(period='2d')
        spy_data = yf.Ticker('SPY').history(period='1mo')
        
        regime = self.regime_detector.detect_regime({
            'vix': vix_data['Close'].iloc[-1] if not vix_data.empty else 15,
            'spx_dd': 0.02,  # Simplified
            'sharpe_30d': 1.0
        })
        
        return {'regime': regime, 'breadth': BreadthCalculator.calculate_breadth()}
    
    def generate_signals(self) -> List[TradeSignal]:
        """Screen Fortune 100 for DIAMOND signals"""
        signals = []
        market = self.get_market_regime()
        
        for symbol in self.fortune_100[:3]:  # Test first 3
            try:
                ticker = yf.Ticker(symbol)
                info = ticker.info
                hist = ticker.history(period='1mo')
                
                if hist.empty or info.get('regularMarketPrice') is None:
                    continue
                    
                price = info['regularMarketPrice']
                
                # Pattern detection
                breakout, pattern_score = PatternDetector.detect_breakout(symbol)
                volume_conf = min(100, hist['Volume'].tail(3).mean() / hist['Volume'].mean() * 50)
                momentum = ((hist['Close'].iloc[-1] - hist['Close'].iloc[-5]) / hist['Close'].iloc[-5]) * 100
                conviction = 75 + (price % 10)  # Simplified
                
                density, threshold = self.signal_density.calculate_density(
                    pattern_score, volume_conf, market['breadth'], 
                    min(100, momentum), conviction
                )
                
                if density >= threshold and self.trades_today < self.max_trades_day:
                    stop_loss = price * 0.98  # 2% stop
                    
                    signal = TradeSignal(
                        symbol=symbol,
                        action="BUY",
                        entry_price=price,
                        stop_loss=stop_loss,
                        density=density,
                        confidence=conviction,
                        risk_pct=self.risk_pct,
                        timestamp=datetime.now().isoformat(),
                        components=self.signal_density.components,
                        regime=market['regime']
                    )
                    
                    signals.append(signal)
                    logger.info(f"💎 {symbol}: {self.signal_density.get_tier(density)} ({density:.1f})")
            
            except Exception as e:
                logger.error(f"Signal error {symbol}: {e}")
        
        return signals
    
    def update_risk_allocation(self):
        """Accordion: Performance earns risk, chaos contracts"""
        if len(self.trade_history) < 10:
            return  # Baby mode
            
        recent_trades = self.trade_history[-20:]
        wins = [t for t in recent_trades if t.pnl and t.pnl > 0]
        win_rate = len(wins) / len(recent_trades)
        avg_density = np.mean([t.density for t in recent_trades])
        
        market = self.get_market_regime()
        
        # Expand on performance
        if win_rate > 0.6 and avg_density > 80:
            self.risk_pct = min(self.max_risk_cap, self.risk_pct + 0.02)
            logger.info(f"📈 Risk expanded: {self.risk_pct*100:.0f}%")
        
        # Contract on chaos/stagnation  
        elif market['regime'] == "CHAOS":
            self.risk_pct *= 0.5
            logger.warning(f"⚠️ CHAOS MODE: Risk cut to {self.risk_pct*100:.0f}%")
        elif market['regime'] == "STAGNATION":
            self.risk_pct *= 0.8
            logger.warning(f"😴 STAGNATION: Risk to {self.risk_pct*100:.0f}%")
        
        self.risk_pct = max(0.02, self.risk_pct)  # 2% floor
    
    def size_position(self, signal: TradeSignal) -> int:
        """Dynamic position sizing by density tier"""
        risk_amount = self.balance * signal.risk_pct
        stop_distance = abs(signal.entry_price - signal.stop_loss)
        
        if stop_distance <= 0:
            return 0
            
        base_size = risk_amount / stop_distance
        
        # Density multiplier
        tier = self.signal_density.get_tier(signal.density)
        multipliers = {"DIAMOND": 1.0, "GOLD": 0.75, "SILVER": 0.5, "BRONZE": 0.25}
        multiplier = multipliers.get(tier, 0.0)
        
        size = int(base_size * multiplier)
        return min(size, 1000)  # Max 1000 shares
    
    def run_daily_cycle(self):
        """Full trading cycle"""
        logger.info("🌙 NIGHT TRADER DAILY CYCLE START")
        
        # Update risk allocation
        self.update_risk_allocation()
        
        # Generate signals
        signals = self.generate_signals()
        
        # Execute highest density first
        signals.sort(key=lambda x: x.density, reverse=True)
        
        for signal in signals:
            qty = self.size_position(signal)
            if qty > 0:
                trade = ExecutedTrade(
                    signal_id=f"{signal.symbol}_{signal.timestamp}",
                    symbol=signal.symbol,
                    action=signal.action,
                    entry_price=signal.entry_price,
                    exit_price=None,
                    quantity=qty,
                    pnl=None,
                    timestamp=datetime.now().isoformat(),
                    status="OPEN",
                    density=signal.density
                )
                
                self.trade_history.append(trade)
                self.trades_today += 1
                
                # Simulate P&L for demo (real would monitor live)
                profit = qty * (signal.entry_price * 0.015)  # 1.5% avg win
                trade.pnl = profit
                trade.status = "CLOSED"
                
                self.balance += profit
                logger.info(f"✅ {signal.symbol}: {self.signal_density.get_tier(signal.density)} | "
                          f"${profit:,.0f} | Balance: ${self.balance:,.0f}")
        
        logger.info(f"🌙 CYCLE COMPLETE | Trades: {self.trades_today} | "
                   f"Balance: ${self.balance:,.0f} | Risk: {self.risk_pct*100:.0f}%")

# MAIN EXECUTION
if __name__ == '__main__':
    trader = NightTraderEngine(initial_balance=100000)
    
    # Run 30-day simulation
    for day in range(30):
        trader.run_daily_cycle()
        trader.trades_today = 0  # Reset daily counter
        logger.info(f"Day {day+1} complete. Balance: ${trader.balance:,.0f}")
    
    logger.info(f"🏆 30-DAY RESULTS: ${trader.balance:,.0f} | "
               f"Growth: {((trader.balance/100000)-1)*100:.1f}% | "
               f"Final Risk: {trader.risk_pct*100:.0f}%")
