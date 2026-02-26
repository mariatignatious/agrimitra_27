import React from 'react';
import './AgentResponse.css';

function PriceResponse({ output }) {
  if (!output) return null;

  // Support both nested `price_info` (legacy) and flat `price_agent` outputs
  const priceInfo = output.price_info || {};
  const currentPriceRaw = output.current_price || priceInfo.current_price || priceInfo.price || output.price || null;
  const unit = output.unit || priceInfo.unit || 'per kg';
  const trend = (output.price_trend || priceInfo.trend || priceInfo.price_trend || 'stable');
  const marketLocation = output.market || priceInfo.market || priceInfo.location || '';

  // Determine trend icon/color/text
  const getTrendInfo = () => {
    const t = trend.toLowerCase();
    if (t.includes('up') || t.includes('rising') || t.includes('increase')) {
      return { icon: '📈', color: '#e74c3c', text: 'Rising' };
    } else if (t.includes('down') || t.includes('falling') || t.includes('decrease')) {
      return { icon: '📉', color: '#3498db', text: 'Falling' };
    }
    return { icon: '➡️', color: '#95a5a6', text: 'Stable' };
  };
  const trendInfo = getTrendInfo();
  const priceChange = output.price_change || priceInfo.price_change || null;
  const recommendation = output.selling_advice || priceInfo.recommendation || priceInfo.suggestion || null;
  const crop = output.crop || priceInfo.crop || '';

  // Format price (handle number or human-readable string)
  let formattedPrice = 'N/A';
  if (currentPriceRaw !== null && currentPriceRaw !== undefined) {
    if (typeof currentPriceRaw === 'number') {
      formattedPrice = `₹${currentPriceRaw.toFixed(2)}`;
    } else if (typeof currentPriceRaw === 'string') {
      // If string already contains currency, trust it
      if (currentPriceRaw.includes('₹')) {
        formattedPrice = currentPriceRaw;
      } else {
        const n = parseFloat(currentPriceRaw.replace(/[^0-9.\-]/g, ''));
        formattedPrice = Number.isFinite(n) ? `₹${n.toFixed(2)}` : currentPriceRaw;
      }
    } else {
      // fallback serialization
      formattedPrice = String(currentPriceRaw);
    }
  }
  // header location text
  const displayCrop = output.commodity_display || crop || '';
  const locParts = [];
  if (output.district) locParts.push(output.district);
  if (output.state) locParts.push(output.state);
  const locationText = locParts.join(', ');
  const headerTitle = displayCrop
    ? `Market Price for ${displayCrop}${locationText ? ' – ' + locationText : ''}`
    : 'Market Price Information';

  // helper to clean units from price string
  const stripUnit = (priceStr) => {
    if (typeof priceStr === 'string') {
      return priceStr.replace(/\/?kg\b/i, '').replace(/per\s*kg\b/i, '').trim();
    }
    return priceStr;
  };
  formattedPrice = stripUnit(formattedPrice);
  let displayUnit = unit;
  if (formattedPrice && typeof formattedPrice === 'string' && displayUnit && formattedPrice.toLowerCase().includes(displayUnit.replace(/per\s*/i, '').replace(/\s+/g, ''))) {
    displayUnit = '';
  }

  // render
  return (
    <div className="agent-response price-response">
      <div className="response-header">
        <div className="header-icon">💰</div>
        <div>
          <h3>{headerTitle}</h3>
          <p className="header-subtitle">Current Market Rates & Trends</p>
        </div>
      </div>

      <div className="response-content">
        <div className="price-card-main">
          <div className="price-display">
            <div className="price-label">Current Price</div>
            <div className="price-value">{formattedPrice}</div>
            <div className="price-unit">{displayUnit}</div>
          </div>

          {output.predicted_price && (
            <div className="predicted-display">
              <div className="price-label">Tomorrow's expected price</div>
              <div className="price-value">
                {(() => {
                  let p = output.predicted_price;
                  if (typeof p === 'string') {
                    p = stripUnit(p);
                  }
                  if (typeof p === 'number') {
                    p = `₹${p.toFixed(2)}`;
                  }
                  return p;
                })()}
              </div>
              <div className="price-unit">{displayUnit}</div>
            </div>
          )}

          <div className="trend-display">
            <span className="trend-icon" style={{ color: trendInfo.color }}>
              {trendInfo.icon}
            </span>
            <span className="trend-text" style={{ color: trendInfo.color }}>
              {trendInfo.text}
            </span>
            {priceChange && (
              <span className="price-change" style={{ color: trendInfo.color }}>
                ({priceChange > 0 ? '+' : ''}{priceChange}%)
              </span>
            )}
          </div>
        </div>

        {marketLocation && (
          <div className="market-info">
            <span className="info-label">📍 Market:</span>
            <span className="info-value">{marketLocation}</span>
          </div>
        )}

        {recommendation && (
          <div className="recommendation-card">
            <h5 className="section-title">💡 Recommendation:</h5>
            <p className="recommendation-text">{recommendation}</p>
          </div>
        )}

        {priceInfo.historical_data && (
          <div className="historical-card">
            <h5 className="section-title">📊 Price History:</h5>
            <div className="historical-data">
              {Array.isArray(priceInfo.historical_data) ? (
                <ul className="historical-list">
                  {priceInfo.historical_data.slice(0, 5).map((item, idx) => (
                    <li key={idx}>
                      {item.date || item.day}: ₹{item.price}
                    </li>
                  ))}
                </ul>
              ) : (
                <p>{JSON.stringify(priceInfo.historical_data)}</p>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );

}

export default PriceResponse;

