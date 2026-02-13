import React, { useState, useEffect } from 'react';
import { View, Text, TextInput, ScrollView, TouchableOpacity, StyleSheet, Alert } from 'react-native';
import Purchases from 'react-native-purchases';

// ============================================================================
// BACKEND URL (Only this - no API keys in app!)
// ============================================================================

const BACKEND_URL = 'https://sauc-e-backend-production.up.railway.app';
const REVENUECAT_PUBLIC_KEY = 'appl_gNFmOHvscXhhhoQWpgDvVPQeLZm'; // Public key, safe
const FREE_MOVE_LIMIT = 10;

const CHEDDAR = () => {
  // ==========================================================================
  // STATE
  // ==========================================================================

  const [isSubscribed, setIsSubscribed] = useState(false);
  const [moveCount, setMoveCount] = useState(0);

  const [question, setQuestion] = useState('');
  const [circle, setCircle] = useState('Survival'); // Survival / Security / Moves
  const [region, setRegion] = useState('US');       // US or Canada

  const [answer, setAnswer] = useState('');
  const [loading, setLoading] = useState(false);
  const [customerId, setCustomerId] = useState(null);

  // ==========================================================================
  // INITIALIZATION
  // ==========================================================================

  useEffect(() => {
    const initTimer = setTimeout(() => {
      initializePurchases();
    }, 500);

    return () => clearTimeout(initTimer);
  }, []);

  async function initializePurchases() {
    try {
      await Purchases.configure({
        apiKey: REVENUECAT_PUBLIC_KEY,
      });

      const cid = await checkSubscriptionStatus();
      await syncUsageCount(cid);

      console.log('RevenueCat initialized for CHEDDAR');
    } catch (error) {
      console.error('RevenueCat init error (CHEDDAR):', error);
    }
  }

  async function syncUsageCount(cid) {
    try {
      const response = await fetch(`${BACKEND_URL}/api/cheddar/usage-status`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ customerId: cid || 'anonymous' }),
      });

      if (response.ok) {
        const data = await response.json();
        setMoveCount(data.usageCount || 0);
      }
    } catch (error) {
      console.log('CHEDDAR usage sync skipped:', error.message);
    }
  }

  async function checkSubscriptionStatus() {
    try {
      const customerInfo = await Purchases.getCustomerInfo();
      const cid = customerInfo.originalAppUserId;
      setCustomerId(cid);

      if (customerInfo.entitlements.active['premium']) {
        setIsSubscribed(true);
      } else {
        setIsSubscribed(false);
      }

      return cid;
    } catch (error) {
      console.error('Subscription check error (CHEDDAR):', error);
      return null;
    }
  }

  // ==========================================================================
  // GET MONEY MOVE (Calls backend, NOT Claude directly)
  // ==========================================================================

  async function handleGetMove() {
    if (!question.trim()) {
      Alert.alert('Error', 'Tell CHEDDAR what is going on with your money.');
      return;
    }

    setLoading(true);

    try {
      const response = await fetch(`${BACKEND_URL}/api/cheddar/get-move`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          customerId: customerId || 'anonymous',
          question,
          circle,
          region,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();

        if (response.status === 403) {
          Alert.alert(
            'Limit Reached',
            'Upgrade to FONDUE for unlimited money moves',
            [
              { text: 'Upgrade', onPress: handleSubscribe },
              { text: 'Cancel', onPress: () => {} },
            ]
          );
          return;
        }

        throw new Error(errorData.error || 'Failed to get money move');
      }

      const data = await response.json();
      setAnswer(data.answer);
      setMoveCount(moveCount + 1);
      setQuestion('');
    } catch (error) {
      Alert.alert('Error', error.message || 'Failed to process request');
    } finally {
      setLoading(false);
    }
  }

  // ==========================================================================
  // SUBSCRIPTION MANAGEMENT (Monthly vs Annual FONDUE)
  // ==========================================================================

  async function handleSubscribe() {
    try {
      const offerings = await Purchases.getOfferings();

      if (!offerings.current || !offerings.current.availablePackages.length) {
        Alert.alert('Unavailable', 'No subscription offerings are available right now.');
        return;
      }

      // Expect RevenueCat packages with types MONTHLY and ANNUAL
      const monthly = offerings.current.availablePackages.find(
        (p) => p.packageType === 'MONTHLY'
      );
      const annual = offerings.current.availablePackages.find(
        (p) => p.packageType === 'ANNUAL'
      );

      if (!monthly && !annual) {
        Alert.alert('Unavailable', 'No monthly or annual plans are configured yet.');
        return;
      }

      const buttons = [];

      if (monthly) {
        buttons.push({
          text: 'Monthly – $6.99',
          onPress: async () => {
            try {
              const { customerInfo } = await Purchases.purchasePackage(monthly);
              if (customerInfo.entitlements.active['premium']) {
                setIsSubscribed(true);
                Alert.alert('Welcome to FONDUE', 'Monthly plan activated.');
              }
            } catch (e) {
              if (!e.userCancelled) {
                Alert.alert('Error', 'Failed to complete monthly purchase');
              }
            }
          },
        });
      }

      if (annual) {
        buttons.push({
          text: 'Annual – $69.99',
          onPress: async () => {
            try {
              const { customerInfo } = await Purchases.purchasePackage(annual);
              if (customerInfo.entitlements.active['premium']) {
                setIsSubscribed(true);
                Alert.alert('Welcome to FONDUE', 'Annual plan activated.');
              }
            } catch (e) {
              if (!e.userCancelled) {
                Alert.alert('Error', 'Failed to complete annual purchase');
              }
            }
          },
        });
      }

      buttons.push({ text: 'Cancel', style: 'cancel' });

      Alert.alert(
        'Choose your FONDUE plan',
        'Unlock all sauces with Monthly or Annual FONDUE.',
        buttons
      );
    } catch (error) {
      console.error('Subscription error (CHEDDAR):', error);
      Alert.alert('Error', 'Unable to load subscription options right now.');
    }
  }

  // ==========================================================================
  // RENDER
  // ==========================================================================

  const circles = ['Survival', 'Security', 'Moves'];
  const regions = ['US', 'Canada'];

  return (
    <View style={styles.container}>
      <ScrollView contentContainerStyle={styles.scrollContent}>
        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.title}>CHEDDAR</Text>
          <Text style={styles.subtitle}>(3,6,9) UP 22</Text>
          <Text style={styles.philosophy}>get rich slow cook+live tryin’</Text>

          {!isSubscribed && (
            <TouchableOpacity style={styles.upgradeButton} onPress={handleSubscribe}>
              <Text style={styles.upgradeText}>
                Premium · {Math.max(0, FREE_MOVE_LIMIT - moveCount)} free moves left
              </Text>
            </TouchableOpacity>
          )}
        </View>

        <View style={styles.content}>
          {/* Circle selection */}
          <Text style={styles.sectionTitle}>Pick a Money Circle</Text>
          {circles.map((c) => (
            <TouchableOpacity
              key={c}
              style={[
                styles.chipButton,
                circle === c && styles.chipButtonActive,
              ]}
              onPress={() => setCircle(c)}
            >
              <Text style={styles.chipText}>{c}</Text>
            </TouchableOpacity>
          ))}

          {/* Region selection */}
          <Text style={styles.sectionTitle}>Where Are You?</Text>
          <View style={styles.regionRow}>
            {regions.map((r) => (
              <TouchableOpacity
                key={r}
                style={[
                  styles.regionButton,
                  region === r && styles.regionButtonActive,
                ]}
                onPress={() => setRegion(r)}
              >
                <Text style={styles.regionText}>{r}</Text>
              </TouchableOpacity>
            ))}
          </View>

          {/* Question input */}
          <Text style={styles.sectionTitle}>Your Money Situation</Text>
          <TextInput
            style={styles.input}
            value={question}
            onChangeText={setQuestion}
            placeholder="Tell CHEDDAR what's going on with your money in 2–3 sentences."
            placeholderTextColor="#999"
            multiline
          />

          {/* Get move button */}
          <TouchableOpacity
            style={[
              styles.moveButton,
              (!question.trim() || loading) && styles.moveButtonDisabled,
            ]}
            onPress={handleGetMove}
            disabled={!question.trim() || loading}
          >
            <Text style={styles.moveButtonText}>
              {loading ? 'Working the numbers...' : 'Get a Money Move'}
            </Text>
          </TouchableOpacity>

          {/* Answer box */}
          {answer !== '' && (
            <View style={styles.answerBox}>
              <Text style={styles.answerTitle}>CHEESE PULL</Text>
              <Text style={styles.answerText}>{answer}</Text>
            </View>
          )}

          {/* Footer */}
          <View style={styles.footer}>
            <Text style={styles.footerText}>Runs on CHEDDAR Sauce 🔥 🧀</Text>
            <Text style={styles.footerSmall}>
              CHEDDAR is for Money · Sample: CATSUP (Learning) • BBQE (Safety) • RELISH (Feelings)
            </Text>
          </View>
        </View>
      </ScrollView>
    </View>
  );
};

// ============================================================================
// STYLES
// ============================================================================

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#121212',
  },
  scrollContent: {
    paddingBottom: 40,
  },
  header: {
    alignItems: 'center',
    paddingTop: 40,
    paddingBottom: 20,
  },
  title: {
    fontSize: 40,
    fontWeight: 'bold',
    color: '#F7C948', // cheddar yellow
    marginBottom: 4,
  },
  subtitle: {
    fontSize: 18,
    color: '#F7C948',
    marginBottom: 4,
  },
  philosophy: {
    fontSize: 12,
    color: '#ccc',
    fontStyle: 'italic',
  },
  upgradeButton: {
    backgroundColor: '#F7C948',
    paddingVertical: 10,
    paddingHorizontal: 24,
    borderRadius: 24,
    alignSelf: 'center',
    marginVertical: 16,
  },
  upgradeText: {
    color: '#1a1a1a',
    fontWeight: '600',
    fontSize: 14,
  },
  content: {
    paddingHorizontal: 20,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: 'white',
    marginTop: 24,
    marginBottom: 12,
  },
  chipButton: {
    backgroundColor: '#333',
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 8,
    borderLeftWidth: 4,
    borderLeftColor: '#F7C948',
    marginBottom: 8,
  },
  chipButtonActive: {
    backgroundColor: '#F7C948',
    borderLeftColor: '#fff',
  },
  chipText: {
    color: 'white',
    fontSize: 14,
    fontWeight: '500',
  },
  regionRow: {
    flexDirection: 'row',
    columnGap: 12,
  },
  regionButton: {
    flex: 1,
    backgroundColor: '#333',
    paddingVertical: 10,
    borderRadius: 8,
    alignItems: 'center',
  },
  regionButtonActive: {
    backgroundColor: '#2ECC71',
  },
  regionText: {
    color: 'white',
    fontSize: 14,
    fontWeight: '500',
  },
  input: {
    backgroundColor: '#333',
    color: 'white',
    borderRadius: 8,
    paddingVertical: 12,
    paddingHorizontal: 16,
    marginVertical: 12,
    minHeight: 120,
    textAlignVertical: 'top',
  },
  moveButton: {
    backgroundColor: '#F7C948',
    paddingVertical: 14,
    borderRadius: 8,
    alignItems: 'center',
    marginVertical: 16,
  },
  moveButtonDisabled: {
    opacity: 0.6,
  },
  moveButtonText: {
    color: '#1a1a1a',
    fontWeight: '700',
    fontSize: 16,
  },
  answerBox: {
    backgroundColor: '#333',
    borderRadius: 8,
    padding: 16,
    marginTop: 20,
    borderLeftWidth: 4,
    borderLeftColor: '#F7C948',
  },
  answerTitle: {
    color: '#F7C948',
    fontWeight: '700',
    marginBottom: 8,
  },
  answerText: {
    color: '#ccc',
    lineHeight: 20,
  },
  footer: {
    alignItems: 'center',
    marginTop: 40,
    paddingTop: 20,
    borderTopWidth: 1,
    borderTopColor: '#333',
  },
  footerText: {
    color: '#F7C948',
    fontWeight: '600',
    marginBottom: 4,
  },
  footerSmall: {
    color: '#999',
    fontSize: 12,
    marginTop: 2,
    textAlign: 'center',
  },
});

export default CHEDDAR;
