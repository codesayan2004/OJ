#include <bits/stdc++.h>
#define int long long
using namespace std;

const int MOD = 1e9 + 7;

void Solve() {
    int n, m;
    cin >> n >> m;
    vector<int> arr(n);
    for (int i = 0; i < n; i++) cin >> arr[i];

    vector<int> prev(m + 2, 0), curr(m + 2, 0);

    // Base case: If last element is 0, it can be any value from 1 to m
    if (arr[n - 1] == 0) {
        for (int j = 1; j <= m; j++) prev[j] = 1;
    } else {
        prev[arr[n - 1]] = 1;
    }

    // Bottom-up DP
    for (int i = n - 2; i >= 0; i--) {
        for (int j = 1; j <= m; j++) {
            if (arr[i] == 0 || arr[i] == j) {
                curr[j] = (prev[j] + (j > 1 ? prev[j - 1] : 0) + (j < m ? prev[j + 1] : 0)) % MOD;
            } else {
                curr[j] = 0;
            }
        }
        swap(prev, curr); // Move to next row
    }

    int ans = 0;
    if (arr[0] == 0) {
        for (int j = 1; j <= m; j++) ans = (ans + prev[j]) % MOD;
    } else {
        ans = prev[arr[0]];
    }

    cout << ans << "\n";
}

signed main() {
    ios::sync_with_stdio(false);
    cin.tie(0);
    Solve();
}