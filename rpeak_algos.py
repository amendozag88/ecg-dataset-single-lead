# CINDY: 2 NEW R-PEAK DETECTOR ALGOS

def sma_detector(window_2s, fs=125):
    fast_win_ms = 80
    fast_win_samples = max(1, int(fast_win_ms * 1e-3 * fs))
    slow_win_ms = 200
    slow_win_samples = max(1, int(slow_win_ms * 1e-3 * fs))
    refractory_ms = 200
    refractory_samples = max(1, int(refractory_ms * 1e-3 * fs))

    fast_sum = 0.0
    slow_sum = 0.0

    history_size = slow_win_samples
    history = [0.0] * history_size
    history_index = 0

    was_above = False
    last_detection_index = -refractory_samples
    out_indices = []

    for n in range(len(window_2s)):
        rectified_val = window_2s[n]
        old_val = history[history_index]
        fast_history_idx = (history_index - fast_win_samples + history_size) % history_size
        fast_old_val = history[fast_history_idx]

        fast_sum = fast_sum + rectified_val - fast_old_val
        slow_sum = slow_sum + rectified_val - old_val

        history[history_index] = rectified_val
        history_index = (history_index + 1) % history_size

        if n < history_size:
            continue

        fast_sma = fast_sum / fast_win_samples
        slow_sma = slow_sum / slow_win_samples

        is_above = (fast_sma > slow_sma)

        if is_above and not was_above:
            if (n - last_detection_index) > refractory_samples:
                search_win = fast_win_samples // 2
                search_start = max(0, n - search_win)
                search_end = min(len(window_2s) - 1, n + search_win // 2)

                rpeak_idx = n
                rpeak_val = -1e9

                for i in range(search_start, search_end + 1):
                    if window_2s[i] > rpeak_val:
                        rpeak_val = window_2s[i]
                        rpeak_idx = i

                out_indices.append(rpeak_idx)
                last_detection_index = n
        was_above = is_above

    return out_indices


def hc_detector(window_2s, fs=125):
    mwi_win_ms = 80
    mwi_win_samples = max(1, int(mwi_win_ms * 1e-3 * fs))
    refractory_ms = 200
    refractory_samples = max(1, int(refractory_ms * 1e-3 * fs))

    spk = 0.0
    npk = 0.0
    threshold = 0.0

    mwi_history = [0.0] * mwi_win_samples
    mwi_index = 0
    mwi_sum = 0.0

    out_indices = []
    last_detection_index = -refractory_samples

    if len(window_2s) == 0:
        return []

    x_prev1 = window_2s[0]
    x_prev2 = x_prev1

    for n in range(len(window_2s)):
        x_n = window_2s[n]

        dx = abs(x_n - x_prev1) + abs(x_n - x_prev2)
        x_prev2 = x_prev1
        x_prev1 = x_n

        old_val = mwi_history[mwi_index]
        mwi_sum = mwi_sum + dx - old_val

        mwi_history[mwi_index] = dx
        mwi_index = (mwi_index + 1) % mwi_win_samples

        if n < mwi_win_samples:
            current_mwi = mwi_sum / mwi_win_samples
            if current_mwi > spk:
                spk = current_mwi
            continue

        mwi_val = mwi_sum / mwi_win_samples
        threshold = npk + 0.3125 * (spk - npk)

        if mwi_val > threshold:
            if (n - last_detection_index) > refractory_samples:
                search_win = mwi_win_samples + 2
                search_start = max(0, n - search_win)
                search_end = n

                rpeak_idx = n
                rpeak_val = -1e9

                for i in range(search_start, search_end + 1):
                    if window_2s[i] > rpeak_val:
                        rpeak_val = window_2s[i]
                        rpeak_idx = i

                out_indices.append(rpeak_idx)
                last_detection_index = n
                spk = 0.125 * mwi_val + 0.875 * spk
        else:
            if (n - last_detection_index) > refractory_samples:
                npk = 0.125 * mwi_val + 0.875 * npk

    return out_indices