from datetime import date
import gamedaybot.utils as utils

def get_scoreboard_short(league, week=None):
    # Gets current week's scoreboard
    box_scores = league.box_scores(week=week)
    score = ['%4s %6.2f - %6.2f %4s' % (i.home_team.team_abbrev, i.home_score,
                                    i.away_score, i.away_team.team_abbrev) for i in box_scores
             if i.away_team]
    text = ['Score Update'] + score
    return '\n'.join(text)


def get_projected_scoreboard(league, week=None):
    # Gets current week's scoreboard projections
    box_scores = league.box_scores(week=week)
    score = ['%4s %6.2f - %6.2f %4s' % (i.home_team.team_abbrev, get_projected_total(i.home_lineup),
                                    get_projected_total(i.away_lineup), i.away_team.team_abbrev) for i in box_scores
             if i.away_team]
    text = ['Approximate Projected Scores'] + score
    return '\n'.join(text)


def get_standings(league, top_half_scoring, week=None):
    standings_txt = ''
    teams = league.teams
    standings = []
    if not top_half_scoring:
        standings = league.standings()
        standings_txt = [f"{pos + 1}: {team.team_name} ({team.wins}-{team.losses})" for
                         pos, team in enumerate(standings)]
    else:
        top_half_totals = {t.team_name: 0 for t in teams}
        if not week:
            week = league.current_week
        for w in range(1, week):
            top_half_totals = top_half_wins(league, top_half_totals, w)

        for t in teams:
            wins = top_half_totals[t.team_name] + t.wins
            standings.append((wins, t.losses, t.team_name))

        standings = sorted(standings, key=lambda tup: tup[0], reverse=True)
        standings_txt = [f"{pos + 1}: {team_name} ({wins}-{losses}) (+{top_half_totals[team_name]})" for
                         pos, (wins, losses, team_name) in enumerate(standings)]
    text = ["Current Standings:"] + standings_txt

    return "\n".join(text)


def top_half_wins(league, top_half_totals, week):
    box_scores = league.box_scores(week=week)

    scores = [(i.home_score, i.home_team.team_name) for i in box_scores] + \
        [(i.away_score, i.away_team.team_name) for i in box_scores if i.away_team]

    scores = sorted(scores, key=lambda tup: tup[0], reverse=True)

    for i in range(0, len(scores)//2):
        points, team_name = scores[i]
        top_half_totals[team_name] += 1

    return top_half_totals


def get_projected_total(lineup):
    total_projected = 0
    for i in lineup:
        if i.slot_position != 'BE' and i.slot_position != 'IR':
            if i.points != 0 or i.game_played > 0:
                total_projected += i.points
            else:
                total_projected += i.projected_points
    return total_projected


def all_played(lineup):
    for i in lineup:
        if i.slot_position != 'BE' and i.slot_position != 'IR' and i.game_played < 100:
            return False
    return True


def get_monitor(league):
    box_scores = league.box_scores()
    monitor = []
    text = ''
    for i in box_scores:
        monitor += scan_roster(i.home_lineup, i.home_team)
        monitor += scan_roster(i.away_lineup, i.away_team)

    if monitor:
        text = ['Starting Players to Monitor: '] + monitor
    else:
        text = ['No Players to Monitor this week. Good Luck!']
    return '\n'.join(text)


def scan_roster(lineup, team):
    count = 0
    players = []
    for i in lineup:
        if i.slot_position != 'BE' and i.slot_position != 'IR' and \
            i.injuryStatus != 'ACTIVE' and i.injuryStatus != 'NORMAL' \
                and i.game_played == 0:

            count += 1
            player = i.position + ' ' + i.name + ' - ' + i.injuryStatus.title().replace('_', ' ')
            players += [player]

    list = ""
    report = ""

    for p in players:
        list += p + "\n"

    if count > 0:
        s = '%s: \n%s \n' % (team.team_name, list[:-1])
        report = [s.lstrip()]

    return report


def scan_inactives(lineup, team):
    count = 0
    players = []
    for i in lineup:
        if (i.slot_position != 'BE' and i.slot_position != 'IR') \
            and (i.injuryStatus == 'OUT' or i.injuryStatus == 'DOUBTFUL' or i.projected_points <= 0) \
                and i.game_played == 0:
                    count += 1
                    players += ['%s %s - %s, %d pts' %
                                (i.position, i.name, i.injuryStatus.title().replace('_', ' '), i.projected_points)]

    inactive_list = ""
    inactives = ""
    for p in players:
        inactive_list += p + "\n"
    if count > 0:
        s = '%s likely inactive starting player(s): \n%s \n' % (team.team_name, inactive_list[:-1])
        inactives = [s.lstrip()]

    return inactives


def get_matchups(league, random_phrase, week=None):
    # Gets current week's Matchups
    matchups = league.box_scores(week=week)

    score = ['%s(%s-%s) vs %s(%s-%s)' % (i.home_team.team_name, i.home_team.wins, i.home_team.losses,
                                         i.away_team.team_name, i.away_team.wins, i.away_team.losses) for i in matchups
             if i.away_team]

    text = ['Matchups'] + score
    if random_phrase:
        text = text + utils.get_random_phrase()
    return '\n'.join(text)


def get_close_scores(league, week=None):
    # Gets current closest scores (15.999 points or closer)
    matchups = league.box_scores(week=week)
    score = []

    for i in matchups:
        if i.away_team:
            diffScore = i.away_score - i.home_score
            if (-16 < diffScore <= 0 and not all_played(i.away_lineup)) or (0 <= diffScore < 16 and not all_played(i.home_lineup)):
                score += ['%4s %6.2f - %6.2f %4s' % (i.home_team.team_abbrev, i.home_score,
                                                 i.away_score, i.away_team.team_abbrev)]
    if not score:
        return('')
    text = ['Close Scores'] + score
    return '\n'.join(text)


def get_waiver_report(league, faab):
    activities = league.recent_activity(50)
    report = []
    today = date.today().strftime('%Y-%m-%d')
    text = ''

    for activity in activities:
        actions = activity.actions
        d2 = date.fromtimestamp(activity.date/1000).strftime('%Y-%m-%d')
        if d2 == today:  # only get waiver activites from today
            if len(actions) == 1 and actions[0][1] == 'WAIVER ADDED':  # player added, but not dropped
                if faab:
                    s = '%s \nADDED %s %s ($%s)\n' % (actions[0][0].team_name,
                                                      actions[0][2].position, actions[0][2].name, actions[0][3])
                else:
                    s = '%s \nADDED %s %s\n' % (actions[0][0].team_name, actions[0][2].position, actions[0][2].name)
                report += [s.lstrip()]
            elif len(actions) > 1:
                if actions[0][1] == 'WAIVER ADDED' or actions[1][1] == 'WAIVER ADDED':
                    if actions[0][1] == 'WAIVER ADDED':
                        if faab:
                            s = '%s \nADDED %s %s ($%s)\nDROPPED %s %s\n' % (
                                actions[0][0].team_name, actions[0][2].position, actions[0][2].name, actions[0][3], actions[1][2].position, actions[1][2].name)
                        else:
                            s = '%s \nADDED %s %s\nDROPPED %s %s\n' % (
                                actions[0][0].team_name, actions[0][2].position, actions[0][2].name, actions[1][2].position, actions[1][2].name)
                    else:
                        if faab:
                            s = '%s \nADDED %s %s ($%s)\nDROPPED %s %s\n' % (
                                actions[0][0].team_name, actions[1][2].position, actions[1][2].name, actions[1][3], actions[0][2].position, actions[0][2].name)
                        else:
                            s = '%s \nADDED %s %s\nDROPPED %s %s\n' % (
                                actions[0][0].team_name, actions[1][2].position, actions[1][2].name, actions[0][2].position, actions[0][2].name)
                    report += [s.lstrip()]

    report.reverse()

    if not report:
        report += ['No waiver transactions']
    else:
        text = ['Waiver Report %s: ' % today] + report

    return '\n'.join(text)


def get_power_rankings(league, week=None):
    # power rankings requires an integer value, so this grabs the current week for that
    if not week:
        week = league.current_week
    # Gets current week's power rankings
    # Using 2 step dominance, as well as a combination of points scored and margin of victory.
    # It's weighted 80/15/5 respectively
    power_rankings = league.power_rankings(week=week)

    score = ['%s (%.1f) - %s' % (i[0], i[1].playoff_pct, i[1].team_name) for i in power_rankings
            if i]
    text = ['Power Rankings (Playoff %)'] + score
    return '\n'.join(text)

def get_luckys(league, week=None):
    box_scores = league.box_scores(week=week)
    weekly_scores = {}
    for i in box_scores:
        if i.home_score > i.away_score:
            weekly_scores[i.home_team] = [i.home_score,'W']
            weekly_scores[i.away_team] = [i.away_score,'L']
        else:
            weekly_scores[i.home_team] = [i.home_score,'L']
            weekly_scores[i.away_team] = [i.away_score,'W']
    weekly_scores = dict(sorted(weekly_scores.items(), key=lambda item: item[1], reverse=True))

    # losses = 0
    # for t in weekly_scores:
    #     print(t.team_name + ': (' + str(len(weekly_scores)-1-losses) + '-' + str(losses) +')')
    #     losses+=1

    losses = 0
    unlucky_team_name = ''
    unlucky_record = ''
    lucky_team_name = ''
    lucky_record = ''
    num_teams = len(weekly_scores)-1

    for t in weekly_scores:
        if weekly_scores[t][1] == 'L':
            unlucky_team_name = t.team_name
            unlucky_record = str(num_teams-losses) + '-' + str(losses)
            break
        losses += 1

    wins = 0
    weekly_scores = dict(sorted(weekly_scores.items(), key=lambda item: item[1]))
    for t in weekly_scores:
        if weekly_scores[t][1] == 'W':
            lucky_team_name = t.team_name
            lucky_record = str(wins) + '-' + str(num_teams - wins)
            break
        wins += 1

    lucky_str = ['🍀 Lucky 🍀']+['%s was %s against the league, but still got the win' % (lucky_team_name, lucky_record)]
    unlucky_str = ['😡 Unlucky 😡']+['%s was %s against the league, but still took an L' % (unlucky_team_name, unlucky_record)]
    return(lucky_str + unlucky_str)

def get_achievers(league, week=None):
    """
    Get the teams with biggest difference from projection
    """
    box_scores = league.box_scores(week=week)
    over_achiever = ''
    under_achiever = ''
    high_achiever_str = ['📈 Overachiever 📈']
    low_achiever_str = ['📉 Underachiever 📉']
    best_performance = -9999
    worst_performance = 9999
    for i in box_scores:
        home_performance = i.home_score - i.home_projected
        away_performance = i.away_score - i.away_projected

        if home_performance > best_performance:
            best_performance = home_performance
            over_achiever = i.home_team.team_name
        if home_performance < worst_performance:
            worst_performance = home_performance
            under_achiever = i.home_team.team_name
        if away_performance > best_performance:
            best_performance = away_performance
            over_achiever = i.away_team.team_name
        if away_performance < worst_performance:
            worst_performance = away_performance
            under_achiever = i.away_team.team_name

    if best_performance > 0:
        high_achiever_str +=['%s was %.2f points over their projection' % (over_achiever, best_performance)]
    else:
        high_achiever_str += 'No team out performed their projection'

    if worst_performance < 0:
        low_achiever_str += ['%s was %.2f points under their projection' % (under_achiever, abs(worst_performance))]
    else:
        low_achiever_str += 'No team was worse than their projection'

    return(high_achiever_str + low_achiever_str)

def get_trophies(league, week=None):
    # Gets trophies for highest score, lowest score, closest score, and biggest win
    matchups = league.box_scores(week=week)
    low_score = 9999
    low_team_name = ''
    high_score = -1
    high_team_name = ''
    closest_score = 9999
    close_winner = ''
    close_loser = ''
    biggest_blowout = -1
    blown_out_team_name = ''
    ownerer_team_name = ''

    for i in matchups:
        if i.home_score > high_score:
            high_score = i.home_score
            high_team_name = i.home_team.team_name
        if i.home_score < low_score:
            low_score = i.home_score
            low_team_name = i.home_team.team_name
        if i.away_score > high_score:
            high_score = i.away_score
            high_team_name = i.away_team.team_name
        if i.away_score < low_score:
            low_score = i.away_score
            low_team_name = i.away_team.team_name
        if i.away_score - i.home_score != 0 and \
                abs(i.away_score - i.home_score) < closest_score:
            closest_score = abs(i.away_score - i.home_score)
            if i.away_score - i.home_score < 0:
                close_winner = i.home_team.team_name
                close_loser = i.away_team.team_name
            else:
                close_winner = i.away_team.team_name
                close_loser = i.home_team.team_name
        if abs(i.away_score - i.home_score) > biggest_blowout:
            biggest_blowout = abs(i.away_score - i.home_score)
            if i.away_score - i.home_score < 0:
                ownerer_team_name = i.home_team.team_name
                blown_out_team_name = i.away_team.team_name
            else:
                ownerer_team_name = i.away_team.team_name
                blown_out_team_name = i.home_team.team_name

    high_score_str = ['👑 High score 👑']+['%s with %.2f points' % (high_team_name, high_score)]
    low_score_str = ['💩 Low score 💩']+['%s with %.2f points' % (low_team_name, low_score)]
    close_score_str = ['😅 Close win 😅']+['%s barely beat %s by %.2f points' % (close_winner, close_loser, closest_score)]
    blowout_str = ['😱 Blow out 😱']+['%s blew out %s by %.2f points' % (ownerer_team_name, blown_out_team_name, biggest_blowout)]

    text = ['Trophies of the week:'] + high_score_str + low_score_str + blowout_str + close_score_str + get_luckys(league, week) + get_achievers(league, week)
    return '\n'.join(text)