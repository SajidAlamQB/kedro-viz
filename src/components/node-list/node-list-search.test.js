import React from 'react';
import { render, fireEvent } from '@testing-library/react';
import { NodeListSearch, mapStateToProps } from './node-list-search';
import { mockState, setup } from '../../utils/state.mock';

describe('NodeListSearch', () => {
  it('renders without crashing', () => {
    const wrapper = setup.shallow(NodeListSearch);
    const search = wrapper.find('.pipeline-nodelist-search');
    expect(search.length).toBe(1);
  });

  it('clears & blurs search bar on pressing escape key', async () => {
    const props = { searchValue: '', onUpdateSearchValue: jest.fn() };
    const { container } = render(<NodeListSearch {...props} />);
    const input = container.querySelector('input');
    const value = 'foobar';
    input.focus();
    fireEvent.change(input, { target: { value } });
    expect(props.onUpdateSearchValue).toHaveBeenCalledWith(value);
    fireEvent.keyDown(input, { key: 'Escape', keyCode: 27 });
    expect(props.onUpdateSearchValue).toHaveBeenLastCalledWith('');
    expect(input).not.toHaveFocus();
  });

  it('focuses when the user types Ctrl+F', () => {
    const { container } = render(<NodeListSearch />);
    const input = container.querySelector('input');
    fireEvent.keyDown(container, { key: 'f', keyCode: 70, ctrlKey: true });
    expect(input).toHaveFocus();
  });

  it('focuses when the user types Cmd+F', () => {
    const { container } = render(<NodeListSearch />);
    const input = container.querySelector('input');
    fireEvent.keyDown(container, { key: 'f', keyCode: 70, metaKey: true });
    expect(input).toHaveFocus();
  });

  it('does not prevent default browser find event if input is already focused', () => {
    const { container } = render(<NodeListSearch />);
    const event = { key: 'f', keyCode: 70, metaKey: true };
    let allowsDefaultEvent = fireEvent.keyDown(container, event);
    expect(allowsDefaultEvent).toBe(false);
    allowsDefaultEvent = fireEvent.keyDown(container, event);
    expect(allowsDefaultEvent).toBe(true);
  });

  it('blurs input if already focused', () => {
    const { container } = render(<NodeListSearch />);
    const input = container.querySelector('input');
    const event = { key: 'f', keyCode: 70, metaKey: true };
    fireEvent.keyDown(container, event);
    expect(input).toHaveFocus();
    fireEvent.keyDown(container, event);
    expect(input).not.toHaveFocus();
  });

  it('maps state to props', () => {
    const expectedResult = {
      theme: expect.any(String),
    };
    expect(mapStateToProps(mockState.animals)).toEqual(expectedResult);
  });
});
