#include <bits/stdc++.h>
#define int long long
#define vi vector<int>
using namespace std;

const int mod = 1e9+7;

void Solve() {
    int n, x;
    cin >> n >> x;
    vi c(n);
    for (int i = 0; i < n; i++) cin >> c[i];

    vector<int> dp(x + 1, 0);
    dp[0] = 1;  // Base case: Only one way to make sum 0 (choose nothing)

    for (int i = 0; i < n; i++) {  // Iterate over coins
        for (int j = c[i]; j <= x; j++) {  // Process each sum
            dp[j] = (dp[j] + dp[j - c[i]]) % mod;
        }
    }

    cout << dp[x] << "\n";
}

signed main() {
    ios::sync_with_stdio(false);
    cin.tie(0);
    Solve();
}