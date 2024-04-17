import React, { useEffect, useState } from 'react';
import { connect } from 'react-redux';
import {
  changeFlag,
  toggleShowFeatureHints,
  toggleIsPrettyName,
  toggleSettingsModal,
} from '../../actions';
import { getFlagsState } from '../../utils/flags';
import SettingsModalRow from './settings-modal-row';
import {
  settings as settingsConfig,
  localStorageName,
  params,
} from '../../config';
import { saveLocalStorage } from '../../store/helpers';
import { localStorageKeyFeatureHintsStep } from '../../components/feature-hints/feature-hints';
import { useGeneratePathname } from '../../utils/hooks/use-generate-pathname';

import Button from '../ui/button';
import Modal from '../ui/modal';

import './settings-modal.scss';
import { isRunningLocally } from '../../utils';

/**
 * Modal to allow users to change the flag settings
 */

const SettingsModal = ({
  flags,
  showFeatureHints,
  isOutdated,
  isPrettyName,
  latestVersion,
  onToggleFlag,
  onToggleShowFeatureHints,
  onToggleIsPrettyName,
  showSettingsModal,
  visible,
}) => {
  const flagData = getFlagsState();
  const [hasNotInteracted, setHasNotInteracted] = useState(true);
  const [hasClickedApplyAndClose, setHasClickApplyAndClose] = useState(false);
  const [isPrettyNameValue, setIsPrettyName] = useState(isPrettyName);
  const [showFeatureHintsValue, setShowFeatureHintsValue] =
    useState(showFeatureHints);
  const [toggleFlags, setToggleFlags] = useState(flags);

  const { toSetQueryParam } = useGeneratePathname();

  useEffect(() => {
    setShowFeatureHintsValue(showFeatureHints);
  }, [showFeatureHints]);

  useEffect(() => {
    let modalTimeout, resetTimeout;

    if (hasClickedApplyAndClose) {
      modalTimeout = setTimeout(() => {
        showSettingsModal(false);
      }, 1500);

      // Delay the reset so the user can't see the button text change.
      resetTimeout = setTimeout(() => {
        const updatedFlags = Object.entries(toggleFlags);
        updatedFlags.map((each) => {
          const [name, value] = each;
          if (name === params.expandAll) {
            toSetQueryParam(params.expandAll, value);
          }

          return onToggleFlag(name, value);
        });

        onToggleIsPrettyName(isPrettyNameValue);
        onToggleShowFeatureHints(showFeatureHintsValue);
        setHasNotInteracted(true);
        setHasClickApplyAndClose(false);

        window.location.reload();
      }, 2000);
    }

    return () => {
      clearTimeout(modalTimeout);
      clearTimeout(resetTimeout);
    };
  }, [
    hasClickedApplyAndClose,
    showFeatureHintsValue,
    isPrettyNameValue,
    onToggleFlag,
    onToggleShowFeatureHints,
    onToggleIsPrettyName,
    showSettingsModal,
    toggleFlags,
    toSetQueryParam,
  ]);

  const resetStateCloseModal = () => {
    showSettingsModal(false);
    setHasNotInteracted(true);
    setToggleFlags(flags);
    setIsPrettyName(isPrettyName);
    setShowFeatureHintsValue(showFeatureHintsValue);
  };

  return (
    <div className="pipeline-settings-modal">
      <Modal
        closeModal={resetStateCloseModal}
        title="Settings"
        visible={visible.settingsModal}
      >
        <div className="pipeline-settings-modal__content">
          <div className="pipeline-settings-modal__group">
            <div className="pipeline-settings-modal__header">
              <div className="pipeline-settings-modal__name">Name</div>
              <div className="pipeline-settings-modal__state">State</div>
              <div className="pipeline-settings-modal__description">
                Description
              </div>
            </div>
            <SettingsModalRow
              id="isPrettyName"
              name={settingsConfig['isPrettyName'].name}
              toggleValue={isPrettyNameValue}
              description={settingsConfig['isPrettyName'].description}
              onToggleChange={(event) => {
                setIsPrettyName(event.target.checked);
                setHasNotInteracted(false);
              }}
            />
            <SettingsModalRow
              id="showFeatureHints"
              name={settingsConfig['showFeatureHints'].name}
              toggleValue={showFeatureHintsValue}
              description={settingsConfig['showFeatureHints'].description}
              onToggleChange={(event) => {
                setShowFeatureHintsValue(event.target.checked);
                setHasNotInteracted(false);

                if (event.target.checked === false) {
                  saveLocalStorage(localStorageName, {
                    [localStorageKeyFeatureHintsStep]: 0,
                  });
                }
              }}
            />
            {flagData.map(({ name, value, description }) => (
              <SettingsModalRow
                description={description}
                id={value}
                key={value}
                name={name}
                onToggleChange={(event) => {
                  setToggleFlags({
                    ...toggleFlags,
                    [value]: event.target.checked,
                  });

                  setHasNotInteracted(false);
                }}
                toggleValue={toggleFlags[value]}
              />
            ))}
            {isRunningLocally() ? (
              isOutdated ? (
                <div className="pipeline-settings-modal__upgrade-reminder">
                  <span>&#8226; Kedro-Viz {latestVersion} is here! </span>
                  <a
                    href="https://github.com/kedro-org/kedro-viz/releases"
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    View release notes
                  </a>
                </div>
              ) : (
                <div className="pipeline-settings-modal__already-latest">
                  <span>
                    &#8226; You are on the latest version of Kedro-Viz (
                    {latestVersion})
                  </span>
                </div>
              )
            ) : null}
          </div>
          <div className="run-details-modal-button-wrapper">
            <Button
              dataTest={'Cancel Button in Settings Modal'}
              mode="secondary"
              onClick={resetStateCloseModal}
              size="small"
            >
              Cancel
            </Button>
            <Button
              dataTest={'Apply changes and close in Settings Modal'}
              disabled={hasNotInteracted}
              onClick={() => {
                setHasClickApplyAndClose(true);
              }}
              mode={hasClickedApplyAndClose ? 'success' : 'primary'}
              size="small"
            >
              {hasClickedApplyAndClose ? (
                <>
                  Changes applied <span className="success-check-mark">✅</span>
                </>
              ) : (
                'Apply changes and close'
              )}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
};

export const mapStateToProps = (state) => ({
  flags: state.flags,
  showFeatureHints: state.showFeatureHints,
  isPrettyName: state.isPrettyName,
  visible: state.visible,
});

export const mapDispatchToProps = (dispatch) => ({
  showSettingsModal: (value) => {
    dispatch(toggleSettingsModal(value));
  },
  onToggleFlag: (name, value) => {
    dispatch(changeFlag(name, value));
  },
  onToggleIsPrettyName: (value) => {
    dispatch(toggleIsPrettyName(value));
  },
  onToggleShowFeatureHints: (value) => {
    dispatch(toggleShowFeatureHints(value));
  },
});

export default connect(mapStateToProps, mapDispatchToProps)(SettingsModal);
